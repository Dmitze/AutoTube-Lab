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
from typing import TYPE_CHECKING, List, Optional

from modules.adapters.retry import retry, RetryableError
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

    @retry(max_retries=3, base_delay=2.0)
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
