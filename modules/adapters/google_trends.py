"""Google Trends adapter using trendspy RSS feed.

Algorithm
---------
RSS Parsing + Normalization (T-025 – T-030):
    1. Fetch RSS via trendspy (no auth required, free)
    2. Parse entries: title → keyword, rank → raw_score
    3. Normalize: raw_score = 1.0 - (rank / total)  → [0.0, 1.0]
    4. Fallback to SyntheticTrendSource on any network error

Complexity: O(n) where n = number of RSS entries

Usage
-----
    from modules.adapters.google_trends import GoogleTrendsTrendSource
    source = GoogleTrendsTrendSource(geo="US")
    signals = source.fetch()  # list[TrendSignal]
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from modules.adapters.base import TrendSourceAdapter
from modules.adapters.retry import RetryableError, retry
from modules.adapters.synthetic import SyntheticTrendSource
from ytaimbot_ml.schemas import TrendSignal

logger = logging.getLogger(__name__)

_DEFAULT_GEO = "US"
_DEFAULT_MAX_RESULTS = 25


class GoogleTrendsTrendSource(TrendSourceAdapter):
    """Fetch trending search topics from Google Trends RSS.

    Parameters
    ----------
    geo:
        Two-letter country code, e.g. ``"US"``, ``"UA"``, ``"GB"``.
        Defaults to ``GOOGLE_TRENDS_GEO`` env var or ``"US"``.
    max_results:
        Maximum number of TrendSignal objects to return.
    seed:
        Seed for the synthetic fallback source.

    Complexity
    ----------
    fetch(): O(n) where n = number of RSS entries returned by trendspy.

    Examples
    --------
    >>> src = GoogleTrendsTrendSource(geo="US")
    >>> signals = src.fetch()
    >>> assert all(0.0 <= s.raw_score <= 1.0 for s in signals)
    """

    def __init__(
        self,
        geo: str | None = None,
        max_results: int = _DEFAULT_MAX_RESULTS,
        seed: int = 42,
    ) -> None:
        self._geo = geo or os.environ.get("GOOGLE_TRENDS_GEO", _DEFAULT_GEO)
        self._max_results = max_results
        self._fallback = SyntheticTrendSource(seed=seed)

    def fetch(self) -> list[TrendSignal]:
        """Return trending TrendSignals from Google Trends RSS.

        Falls back to SyntheticTrendSource when network is unavailable
        or all retries are exhausted.

        Complexity: O(n)
        """
        try:
            return self._fetch_from_rss()
        except Exception as exc:
            logger.warning(
                "GoogleTrends fetch failed (%s); falling back to synthetic", exc
            )
            return self._fallback.fetch()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @retry(max_retries=3, base_delay=2.0, seed=42)
    def _fetch_from_rss(self) -> list[TrendSignal]:
        """Parse trendspy RSS → list[TrendSignal].

        Raises
        ------
        RetryableError
            On 429 / 5xx / network timeout.
        """
        try:
            import trendspy  # noqa: PLC0415 — optional dep
        except ImportError as exc:
            logger.warning("trendspy not installed: %s", exc)
            return self._fallback.fetch()

        try:
            trends = trendspy.Trends()
            data = trends.trending_now(geo=self._geo)
        except Exception as exc:
            _msg = str(exc).lower()
            if any(kw in _msg for kw in ("429", "rate", "timeout", "connection")):
                raise RetryableError(f"Google Trends rate-limited: {exc}") from exc
            raise

        entries = data if isinstance(data, list) else []
        signals = self._parse_entries(entries)
        logger.info(
            "GoogleTrends: fetched %d signals (geo=%s)", len(signals), self._geo
        )
        return signals[: self._max_results]

    def _parse_entries(self, entries: list) -> list[TrendSignal]:
        """Convert raw trendspy entries → list[TrendSignal].

        Normalization: raw_score = 1.0 - (rank / total)
        So rank 0 (most trending) → score 1.0.

        Complexity: O(n)
        """
        total = max(len(entries), 1)
        now = datetime.now(timezone.utc).isoformat()
        signals: list[TrendSignal] = []

        for rank, entry in enumerate(entries):
            keyword = self._extract_keyword(entry)
            if not keyword:
                continue

            raw_score = 1.0 - (rank / total)

            signals.append(
                TrendSignal(
                    trend_id=f"gt_{keyword.lower().replace(' ', '_')}_{rank}",
                    keyword=keyword,
                    raw_score=float(raw_score),
                    source="google_trends",
                    timestamp=now,
                )
            )

        return signals

    @staticmethod
    def _extract_keyword(entry: object) -> str:
        """Extract keyword string from a trendspy entry (flexible format)."""
        if isinstance(entry, str):
            return entry.strip()
        if hasattr(entry, "keyword"):
            return str(entry.keyword).strip()
        if hasattr(entry, "title"):
            return str(entry.title).strip()
        if isinstance(entry, dict):
            return str(entry.get("keyword") or entry.get("title", "")).strip()
        return str(entry).strip()
