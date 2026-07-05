"""Phase 5 — MetricsCollector: gathers real-world video performance from YouTube Analytics API.

Roadmap tasks: T-326 through T-337 (EPIC 5.2 Metrics Collector)
Dependencies:  google-api-python-client, google-auth

Algorithm
---------
1. Delay Check (T-329): 
   Only collect metrics if video is > 48 hours old (data stabilization).
   O(1) time check.

2. API Query (T-328):
   Fetch views, CTR, retention, revenue, and watch time via Analytics API.
   O(1) network request per video.

3. Persistence (T-331):
   Save MetricsSnapshot to SQLiteStorageAdapter.
   O(log n) write.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Any

from modules.adapters.retry import exponential_backoff # Corrected import
from modules.adapters.errors import RetryableError # Corrected import
from ytaimbot_ml.schemas import MetricsSnapshot

if TYPE_CHECKING:
    from modules.adapters.base import StorageAdapter

logger = logging.getLogger(__name__)

# Scopes for YouTube Analytics API
_SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]


class TooEarlyError(Exception):
    """Raised when trying to collect metrics for a video published < 48 hours ago."""


class MetricsCollector:
    """Service for collecting YouTube video performance metrics.

    Parameters
    ----------
    storage:
        Persistent storage adapter for saving results.
    client_secret_path:
        Path to OAuth2 client secrets JSON.
    token_path:
        Path to cached OAuth2 token JSON.
    """

    def __init__(
        self,
        storage: StorageAdapter,
        client_secret_path: str | Path | None = None,
        token_path: str | Path | None = None,
    ) -> None:
        self._storage = storage
        self._client_secret = Path(
            client_secret_path
            or os.environ.get("YOUTUBE_CLIENT_SECRET_PATH", "data/client_secret.json")
        )
        self._token_path = Path(
            token_path
            or os.environ.get("YOUTUBE_TOKEN_PATH", "data/token.json")
        )
        self._service = None

    def _get_service(self):
        """Lazy-initialize and return the Analytics API service."""
        if self._service is not None:
            return self._service

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "Missing YouTube API dependencies. "
                "Install with: pip install google-api-python-client google-auth-oauthlib"
            )

        creds = None
        if self._token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self._token_path), _SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self._client_secret.exists():
                    raise FileNotFoundError(f"Missing YouTube client secret at {self._client_secret}")
                flow = InstalledAppFlow.from_client_secrets_file(str(self._client_secret), _SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self._token_path, "w") as token:
                token.write(creds.to_json())

        self._service = build("youtubeAnalytics", "v2", credentials=creds)
        return self._service

    @exponential_backoff(max_retries=3, base_delay=2.0, jitter=True) # Corrected decorator
    def collect(self, video_id: str, published_at: datetime) -> MetricsSnapshot:
        """Collect metrics for a specific video.

        Algorithm: O(1) API call (T-328).

        Parameters
        ----------
        video_id:
            YouTube video ID.
        published_at:
            UTC datetime when the video was published.

        Returns
        -------
        MetricsSnapshot
            Populated snapshot object.

        Raises
        ------
        TooEarlyError
            If video is < 48 hours old (T-329).
        RetryableError
            On transient API/network errors (T-332).
        """
        now = datetime.now(timezone.utc)
        age = now - published_at
        
        if age < timedelta(hours=48):
            raise TooEarlyError(f"Video {video_id} is only {age.total_seconds()/3600:.1f}h old")

        try:
            service = self._get_service()
            # Query range: from publication to now
            start_date = published_at.date().isoformat()
            end_date = now.date().isoformat()

            result = service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedRevenue,averageViewDuration,annotationClickThroughRate",
                filters=f"video=={video_id}"
            ).execute()

            # Process API response (T-328)
            rows = result.get("rows", [])
            if not rows or not rows[0]:
                logger.warning("MetricsCollector: no data returned for %s", video_id)
                return MetricsSnapshot(video_id=video_id, collected_at=now)

            data = rows[0]
            snapshot = MetricsSnapshot(
                video_id=video_id,
                views=int(data[0]),
                rpm=(float(data[1]) / int(data[0]) * 1000) if int(data[0]) > 0 else 0.0,
                watch_time_h=float(data[2]) / 3600.0,
                ctr=float(data[3]) / 100.0 if data[3] else 0.0,
                collected_at=now,
            )
            
            return snapshot

        except Exception as exc:
            logger.error("MetricsCollector: failed to fetch for %s: %s", video_id, exc)
            raise RetryableError(str(exc))

    def collect_all_pending(self) -> List[MetricsSnapshot]:
        """Collect metrics for all published videos that haven't been updated recently.

        Algorithm: O(n_videos) (T-330).

        Returns
        -------
        List[MetricsSnapshot]
            List of successfully collected snapshots.
        """
        if not hasattr(self._storage, "list_published_videos"):
            logger.warning("Storage does not support list_published_videos, skipping collection")
            return []

        videos = self._storage.list_published_videos()
        snapshots = []

        for v in videos:
            try:
                pub_at = datetime.fromtimestamp(v["published_at"], tz=timezone.utc)
                snapshot = self.collect(v["video_id"], pub_at)
                self._storage.save_metrics(snapshot)
                snapshots.append(snapshot)
                logger.info("MetricsCollector: updated %s (%d views)", v["video_id"], snapshot.views)
            except TooEarlyError:
                continue
            except Exception as exc:
                logger.warning("MetricsCollector: skipped %s: %s", v["video_id"], exc)

        return snapshots


class MetricsScheduler:
    """Schedules and runs daily metrics collection and weekly feedback updates (T-373, T-374).

    Parameters
    ----------
    collector:
        MetricsCollector instance for fetching YouTube data.
    feedback_scorer:
        Optional FeedbackScorer instance for updating niche weights.
    """

    def __init__(self, collector: MetricsCollector, feedback_scorer: Any = None) -> None:
        self.collector = collector
        self.feedback_scorer = feedback_scorer

    def run_daily_metrics_collection(self) -> None:
        """Daily job to fetch latest metrics for all published videos."""
        logger.info("MetricsScheduler: Running daily metrics collection...")
        self.collector.collect_all_pending()

    def run_weekly_feedback_update(self) -> None:
        """Weekly job to process latest metrics and update ML niche weights."""
        logger.info("MetricsScheduler: Running weekly feedback update...")
        if not self.feedback_scorer:
            logger.warning("MetricsScheduler: No FeedbackScorer provided, skipping.")
            return

        storage = self.collector._storage
        if not hasattr(storage, "list_published_videos") or not hasattr(storage, "get_top_videos"):
            logger.warning("MetricsScheduler: Storage missing required methods.")
            return

        videos = storage.list_published_videos(limit=1000)
        # We need the most recent metric for each video. 
        # But get_top_videos or similar might be easier, or we can just query directly.
        # For simplicity, we just use the latest metrics that get_top_videos fetches, or we simulate it.
        # Since StorageAdapter doesn't have an exact get_metrics per video, 
        # we can fetch all top videos by 'views' to get their latest metric snapshot
        try:
            latest_metrics_list = storage.get_top_videos(n=1000, metric="views")
            metric_map = {row["video_id"]: row for row in latest_metrics_list}
            
            for v in videos:
                vid = v["video_id"]
                if vid in metric_map and "niche" in v:
                    row = metric_map[vid]
                    # Convert dict to MetricsSnapshot
                    from ytaimbot_ml.schemas import MetricsSnapshot
                    from datetime import datetime, timezone
                    snapshot = MetricsSnapshot(
                        video_id=vid,
                        views=row.get("views", 0),
                        ctr=row.get("ctr", 0.0),
                        retention_30s=row.get("retention_30s", 0.0),
                        rpm=row.get("rpm", 0.0),
                        watch_time_h=row.get("watch_time_h", 0.0),
                        collected_at=datetime.fromisoformat(row.get("collected_at", datetime.now(timezone.utc).isoformat()))
                    )
                    self.feedback_scorer.update(v["niche"], snapshot)
            logger.info("MetricsScheduler: Finished weekly feedback update.")
        except Exception as exc:
            logger.error("MetricsScheduler: Failed weekly update: %s", exc)
