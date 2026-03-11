"""YouTube Data API v3 trend source adapter.

Algorithm
---------
QuotaTracker — Sliding Window Counter (T-038):
    Tracks daily API unit consumption.
    window = 86 400 s (1 day), budget = 10 000 units/day.
    Each search.list call costs 100 units.

    can_proceed(units) → bool:
        Drop expired timestamps → O(k expired).
        Sum remaining → O(n active).
    → O(1) amortised per call.

Complexity (fetch): O(n) where n = number of video items returned.

Usage
-----
    import os
    os.environ["YOUTUBE_API_KEY"] = "AIza..."

    from modules.adapters.youtube_search import YouTubeSearchTrendSource
    src = YouTubeSearchTrendSource(query="python tutorial")
    signals = src.fetch()
"""

from __future__ import annotations

import collections
import logging
import os
import time
from collections import deque
from datetime import datetime, timezone

from modules.adapters.base import TrendSourceAdapter
from modules.adapters.retry import NonRetryableError, RetryableError, retry
from modules.adapters.synthetic import SyntheticTrendSource
from ytaimbot_ml.schemas import TrendSignal

logger = logging.getLogger(__name__)

_SEARCH_LIST_UNITS = 100   # each search.list call costs 100 units
_DAILY_QUOTA = 10_000       # free YouTube Data API quota
_WINDOW_SECONDS = 86_400    # 1 day


class QuotaTracker:
    """Sliding-Window Counter for YouTube API quota.

    Parameters
    ----------
    daily_budget:
        Maximum API units per rolling 24 h window.

    Complexity
    ----------
    can_proceed / record: O(k) where k = expired entries (amortised O(1)).

    Examples
    --------
    >>> qt = QuotaTracker(daily_budget=10_000)
    >>> assert qt.can_proceed(100)
    >>> qt.record(100)
    >>> assert qt.remaining >= 9_900
    """

    def __init__(self, daily_budget: int = _DAILY_QUOTA) -> None:
        self._budget = daily_budget
        self._window = _WINDOW_SECONDS
        # deque of (timestamp: float, units: int)
        self._log: deque[tuple[float, int]] = collections.deque()

    def _evict_expired(self) -> None:
        """Remove records older than the rolling window.  O(k expired)."""
        cutoff = time.monotonic() - self._window
        while self._log and self._log[0][0] < cutoff:
            self._log.popleft()

    def can_proceed(self, units: int = _SEARCH_LIST_UNITS) -> bool:
        """Return ``True`` iff spending *units* stays within the daily budget."""
        self._evict_expired()
        used = sum(u for _, u in self._log)
        return used + units <= self._budget

    def record(self, units: int = _SEARCH_LIST_UNITS) -> None:
        """Record that *units* API units were consumed now."""
        self._log.append((time.monotonic(), units))

    @property
    def remaining(self) -> int:
        """Remaining API units in the current window."""
        self._evict_expired()
        used = sum(u for _, u in self._log)
        return self._budget - used


class YouTubeSearchTrendSource(TrendSourceAdapter):
    """Fetch trending topics via YouTube Data API v3 ``search.list``.

    Parameters
    ----------
    query:
        Search query string.  Defaults to ``"trending today"``; override
        to target a specific niche.
    max_results:
        Number of results per API call (max 50 per YouTube policy).
    api_key:
        YouTube Data API v3 key.  Falls back to ``YOUTUBE_API_KEY`` env var.
        When absent, the adapter degrades to :class:`SyntheticTrendSource`.

    Complexity
    ----------
    fetch(): O(n) where n = ``max_results``.

    Examples
    --------
    >>> import os; os.environ["YOUTUBE_API_KEY"] = ""
    >>> src = YouTubeSearchTrendSource()
    >>> signals = src.fetch()          # returns synthetic data (no key)
    >>> assert len(signals) >= 1
    """

    def __init__(
        self,
        query: str = "trending today",
        max_results: int = 25,
        api_key: str | None = None,
        seed: int = 42,
    ) -> None:
        self._query = query
        self._max_results = min(max_results, 50)  # YouTube cap
        self._api_key = api_key or os.environ.get("YOUTUBE_API_KEY", "")
        self._quota = QuotaTracker()
        self._fallback = SyntheticTrendSource(seed=seed)

    @retry(max_retries=3, base_delay=2.0, seed=42)
    def fetch(self) -> list[TrendSignal]:
        """Return trend signals from YouTube search.

        Degrades gracefully:
          1. No API key → returns synthetic data immediately.
          2. Quota exhausted → returns synthetic data with WARNING log.
          3. 429 / 5xx → RetryableError (retry decorator handles backoff).
          4. 400 / 403 → NonRetryableError (no retry).

        Complexity: O(n)
        """
        if not self._api_key:
            logger.warning(
                "YOUTUBE_API_KEY not set; using synthetic trend source"
            )
            return self._fallback.fetch()

        if not self._quota.can_proceed():
            logger.warning(
                "YouTube quota exhausted (%d remaining); using synthetic source",
                self._quota.remaining,
            )
            return self._fallback.fetch()

        return self._call_api()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_api(self) -> list[TrendSignal]:
        """Execute search.list and parse results.

        Raises
        ------
        RetryableError
            On 429 / 500-series HTTP errors.
        NonRetryableError
            On 400 / 403 (bad key, permission denied).
        """
        try:
            from googleapiclient.discovery import build  # noqa: PLC0415
            from googleapiclient.errors import HttpError  # noqa: PLC0415
        except ImportError:
            logger.warning("google-api-python-client not installed; using synthetic")
            return self._fallback.fetch()

        try:
            service = build("youtube", "v3", developerKey=self._api_key)
            response = (
                service.search()
                .list(
                    q=self._query,
                    part="snippet",
                    type="video",
                    order="viewCount",
                    maxResults=self._max_results,
                )
                .execute()
            )
        except Exception as exc:  # noqa: BLE001
            self._handle_api_error(exc)
            return self._fallback.fetch()

        self._quota.record(_SEARCH_LIST_UNITS)
        logger.info(
            "YouTubeSearch: fetched %d items (query=%r, remaining=%d units)",
            len(response.get("items", [])),
            self._query,
            self._quota.remaining,
        )
        return self._parse_response(response)

    @staticmethod
    def _handle_api_error(exc: Exception) -> None:
        """Classify and re-raise API errors as Retryable / NonRetryable."""
        msg = str(exc).lower()
        code = getattr(exc, "resp", None)
        status = int(getattr(code, "status", 0)) if code else 0

        if status in (400, 403) or "invalid" in msg or "forbidden" in msg:
            raise NonRetryableError(f"YouTube API permanent error: {exc}") from exc
        if status == 429 or "quota" in msg or "rate" in msg:
            raise RetryableError(f"YouTube API rate-limit: {exc}") from exc
        if status >= 500 or "timeout" in msg or "connection" in msg:
            raise RetryableError(f"YouTube API transient error: {exc}") from exc
        # Unknown — log and fall through to fallback
        logger.warning("YouTube API unknown error: %s", exc)

    def _parse_response(self, response: dict) -> list[TrendSignal]:
        """Convert API response items → list[TrendSignal].

        Normalization: raw_score = 1.0 - (rank / total) → [0.0, 1.0].

        Complexity: O(n)
        """
        items = response.get("items", [])
        total = max(len(items), 1)
        now = datetime.now(timezone.utc).isoformat()
        signals: list[TrendSignal] = []

        for rank, item in enumerate(items):
            snippet = item.get("snippet", {})
            title = snippet.get("title", "").strip()
            video_id = item.get("id", {}).get("videoId", "")
            if not title:
                continue

            raw_score = 1.0 - (rank / total)
            signals.append(
                TrendSignal(
                    trend_id=f"yt_{video_id or rank}",
                    keyword=title,
                    raw_score=float(raw_score),
                    source="youtube_search",
                    timestamp=now,
                )
            )

        return signals
