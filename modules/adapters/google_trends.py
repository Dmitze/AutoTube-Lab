"""Google Trends adapter for fetching trend signals.

Uses the ``trendspy`` library (not pytrends).  See ADR-0003.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import trendspy
from modules.adapters.base import TrendSourceAdapter
from modules.adapters.errors import RetryableError
from modules.adapters.retry import exponential_backoff
from ytaimbot_ml.schemas import TrendSignal


class GoogleTrendsTrendSource(TrendSourceAdapter):
    """Fetch trending searches from Google Trends via the ``trendspy`` library.

    Uses ``trendspy.Trends().trending_now()`` which returns a list of
    ``TrendKeyword`` objects with ``keyword``, ``volume``, and
    ``started_timestamp`` attributes.

    Parameters
    ----------
    geo:
        ISO 3166-1 alpha-2 country code, e.g. ``"US"`` or ``"UA"``.
    fallback_source:
        Optional :class:`TrendSourceAdapter` used when all retries are
        exhausted.
    max_results:
        Maximum number of signals to return.  ``0`` means unlimited.
    seed:
        Reserved for interface compatibility; not used internally.
    """

    # Volume is an integer (search volume estimate).  Normalise to [0, 1]
    # against this cap so that ``raw_score`` stays in range.
    _VOLUME_CAP: int = 10_000_000

    def __init__(
        self,
        geo: str = "US",
        fallback_source: TrendSourceAdapter | None = None,
        max_results: int = 0,
        seed: int = 42,
    ) -> None:
        self._geo = geo
        self._fallback_source = fallback_source
        self._max_results = max_results
        self._seed = seed  # kept for API compatibility

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @exponential_backoff(max_retries=3, base_delay=2.0, jitter=True, seed=42)
    def _fetch_with_retries(self) -> list[TrendSignal]:
        """Call the Google Trends API and convert results to TrendSignals."""
        client = trendspy.Trends()
        items = client.trending_now(geo=self._geo)

        signals: list[TrendSignal] = []
        for item in items:
            keyword: str = item.keyword

            # volume is an int (may be 0 / None for "no traffic")
            volume: int = item.volume or 0
            raw_score: float = min(volume / self._VOLUME_CAP, 1.0)

            # started_timestamp is a list of Unix epoch ints
            ts_list = item.started_timestamp or []
            if ts_list:
                dt = datetime.fromtimestamp(ts_list[0], tz=timezone.utc)
                timestamp = dt.isoformat(timespec="seconds").replace("+00:00", "Z")
            else:
                timestamp = (
                    datetime.now(timezone.utc)
                    .isoformat(timespec="seconds")
                    .replace("+00:00", "Z")
                )

            trend_id = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")

            signals.append(
                TrendSignal(
                    trend_id=trend_id,
                    keyword=keyword,
                    raw_score=raw_score,
                    source="Google Trends",
                    timestamp=timestamp,
                )
            )

        if self._max_results and len(signals) > self._max_results:
            signals = signals[: self._max_results]

        return signals

    # ------------------------------------------------------------------
    # TrendSourceAdapter
    # ------------------------------------------------------------------

    def fetch(self) -> list[TrendSignal]:
        """Return a list of :class:`~ytaimbot_ml.schemas.TrendSignal` objects.

        Complexity: O(N) where N is the number of trending items returned
        by the Google Trends API.
        """
        try:
            return self._fetch_with_retries()
        except RetryableError:
            if self._fallback_source:
                return self._fallback_source.fetch()
            raise


# ---------------------------------------------------------------------------
# Backward-compatibility alias
# ---------------------------------------------------------------------------
GoogleTrendsAdapter = GoogleTrendsTrendSource
