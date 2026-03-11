"""YouTubeAnalyticsAdapter: fetch video performance stats via YouTube Analytics API.

Roadmap tasks: T-411 through T-430 (EPIC 4.3 Analytics)
Dependencies:  google-api-python-client, google-auth-oauthlib

Metrics fetched (YouTube Analytics API v2):
  - views          : total view count
  - estimatedMinutesWatched : for retention estimation
  - averageViewDuration     : seconds (retention_30s ≈ avg_view_dur / 30)
  - impressionClickThroughRate : CTR in [0, 1]
  - likes          : total likes

EMA smoothing (Exponential Moving Average):
  Algorithm:  ema_t = α × metric_t + (1 − α) × ema_{t-1}
  α default:  0.3 (more weight to recent values)
  Complexity: O(1) per update

Design decisions:
  - Returns ChannelStats dataclass (schemas.py)
  - Falls back to zero-stats on any API error (non-fatal)
  - Caches last known stats in _cache dict (plan_id → ChannelStats)
  - YTAIMBOT_DRY_RUN=true → returns synthetic stats (all zeros)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

from ytaimbot_ml.schemas import ChannelStats

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


class YouTubeAnalyticsAdapter:
    """Fetch and smooth video performance metrics from YouTube Analytics API.

    Parameters
    ----------
    client_secret_path:
        Path to OAuth2 client_secret.json.
    token_path:
        Path to cached token.json.
    ema_alpha:
        EMA smoothing factor α ∈ (0, 1].  Higher = more reactive.
    dry_run:
        When True, ``get_stats()`` returns zero-filled ChannelStats.

    Complexity
    ----------
    get_stats():  O(1) per call — single API request + O(1) EMA update
    get_batch():  O(n) — n video_ids

    Examples
    --------
    >>> adapter = YouTubeAnalyticsAdapter(dry_run=True)
    >>> stats = adapter.get_stats("dQw4w9WgXcQ")
    >>> stats.video_id
    'dQw4w9WgXcQ'
    >>> stats.views
    0
    """

    def __init__(
        self,
        client_secret_path: str | None = None,
        token_path: str | None = None,
        ema_alpha: float = 0.3,
        dry_run: bool | None = None,
    ) -> None:
        from pathlib import Path

        self._client_secret = Path(
            client_secret_path
            or os.environ.get("YOUTUBE_CLIENT_SECRET_PATH", "data/client_secret.json")
        )
        self._token_path = Path(
            token_path
            or os.environ.get("YOUTUBE_TOKEN_PATH", "data/token.json")
        )
        self._alpha = ema_alpha
        self._cache: dict[str, ChannelStats] = {}

        if dry_run is not None:
            self.dry_run = dry_run
        else:
            self.dry_run = os.environ.get("YTAIMBOT_DRY_RUN", "true").lower() != "false"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_stats(self, video_id: str) -> ChannelStats:
        """Fetch analytics for a single video, apply EMA smoothing.

        Parameters
        ----------
        video_id:
            YouTube video ID (11 chars, e.g. ``"dQw4w9WgXcQ"``).

        Returns
        -------
        ChannelStats
            EMA-smoothed metrics.  Zero-filled on dry_run or API error.

        Complexity: O(1)

        Examples
        --------
        >>> adapter = YouTubeAnalyticsAdapter(dry_run=True)
        >>> stats = adapter.get_stats("abc123")
        >>> isinstance(stats, ChannelStats)
        True
        """
        if self.dry_run:
            return ChannelStats(video_id=video_id)

        try:
            raw = self._fetch_raw(video_id)
            smoothed = self._apply_ema(video_id, raw)
            self._cache[video_id] = smoothed
            return smoothed
        except Exception as exc:  # noqa: BLE001
            logger.warning("Analytics fetch failed for %s: %s", video_id, exc)
            return self._cache.get(video_id, ChannelStats(video_id=video_id))

    def get_batch(self, video_ids: list[str]) -> dict[str, ChannelStats]:
        """Fetch analytics for multiple videos.

        Parameters
        ----------
        video_ids:
            List of YouTube video IDs.

        Returns
        -------
        dict[str, ChannelStats]
            Mapping video_id → ChannelStats.

        Complexity: O(n) — n sequential API calls

        Examples
        --------
        >>> adapter = YouTubeAnalyticsAdapter(dry_run=True)
        >>> results = adapter.get_batch(["v1", "v2"])
        >>> len(results)
        2
        """
        return {vid: self.get_stats(vid) for vid in video_ids}

    def meets_kpis(self, video_id: str) -> bool:
        """Return True if the video meets CTR ≥ 6% and retention_30s ≥ 70%.

        Complexity: O(1)

        Examples
        --------
        >>> adapter = YouTubeAnalyticsAdapter(dry_run=True)
        >>> adapter.meets_kpis("abc")
        False
        """
        return self.get_stats(video_id).meets_targets

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_service(self):
        """Build the YouTube Analytics API v2 service.

        Complexity: O(1)
        """
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ImportError(
                "google-api-python-client required. "
                "Install: pip install google-api-python-client google-auth-oauthlib"
            ) from exc

        from modules.adapters.publisher.youtube_upload import YouTubeUploadAdapter
        # Reuse credential logic from upload adapter (DRY principle)
        tmp = YouTubeUploadAdapter(
            client_secret_path=self._client_secret,
            token_path=self._token_path,
            dry_run=False,
        )
        creds = tmp._get_credentials()
        return build("youtubeAnalytics", "v2", credentials=creds)

    def _fetch_raw(self, video_id: str) -> ChannelStats:
        """Fetch raw metrics from YouTube Analytics API.

        Uses ``reports.query`` with dimensions=video, metrics=views+ctr+retention.

        Complexity: O(1) — single HTTP request
        """
        youtube_analytics = self._build_service()

        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=28)).strftime("%Y-%m-%d")

        response = (
            youtube_analytics.reports()
            .query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics=(
                    "views,"
                    "estimatedMinutesWatched,"
                    "averageViewDuration,"
                    "impressionClickThroughRate,"
                    "likes,"
                    "comments"
                ),
                dimensions="video",
                filters=f"video=={video_id}",
            )
            .execute()
        )

        rows = response.get("rows", [])
        if not rows:
            return ChannelStats(video_id=video_id)

        row = rows[0]
        views = int(row[1])
        avg_duration = float(row[3])
        ctr = float(row[4]) / 100.0  # API returns percentage
        retention_30s = min(avg_duration / 30.0, 1.0)
        likes = int(row[5])
        comments = int(row[6]) if len(row) > 6 else 0

        return ChannelStats(
            video_id=video_id,
            views=views,
            ctr=ctr,
            retention_30s=retention_30s,
            likes=likes,
            comments=comments,
        )

    def _apply_ema(self, video_id: str, new_stats: ChannelStats) -> ChannelStats:
        """Apply EMA smoothing to new stats using cached previous values.

        EMA formula: ema_t = α × x_t + (1 − α) × ema_{t-1}

        If no previous stats cached, returns new_stats as-is (cold start).

        Complexity: O(1)
        """
        prev = self._cache.get(video_id)
        if prev is None:
            return new_stats

        a = self._alpha

        def _ema(new: float, old: float) -> float:
            return a * new + (1.0 - a) * old

        return ChannelStats(
            video_id=video_id,
            views=new_stats.views,  # raw count, no smoothing for integers
            ctr=_ema(new_stats.ctr, prev.ctr),
            retention_30s=_ema(new_stats.retention_30s, prev.retention_30s),
            likes=new_stats.likes,
            comments=new_stats.comments,
        )
