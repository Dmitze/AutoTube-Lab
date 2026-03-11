"""Composite trend adapter — K-way merge of multiple TrendSourceAdapters.

Algorithm
---------
K-way Merge with Deduplication (T-051 – T-055):
    1. Collect all signals from all adapters  → O(Σ n_i)
    2. Deduplicate by normalised keyword:       → O(total)
       key = keyword.lower().strip()
       keep the signal with the highest score
    3. Apply per-adapter weight multiplier      → O(total)
    4. Sort descending by raw_score             → O(total log total)

    Total: O(N log N) where N = sum of all adapter signal counts.

Usage
-----
    from modules.adapters.composite import CompositeTrendSource
    from modules.adapters.google_trends import GoogleTrendsTrendSource
    from modules.adapters.youtube_search import YouTubeSearchTrendSource

    src = CompositeTrendSource(
        adapters=[
            (GoogleTrendsTrendSource(geo="US"), 1.0),
            (YouTubeSearchTrendSource(),         1.0),
        ]
    )
    signals = src.fetch()
"""

from __future__ import annotations

import logging

from modules.adapters.base import TrendSourceAdapter
from modules.adapters.cache import TrendCache
from modules.adapters.synthetic import SyntheticTrendSource
from ytaimbot_ml.schemas import TrendSignal

logger = logging.getLogger(__name__)

_CACHE_TTL = 900   # seconds (15 minutes)


class CompositeTrendSource(TrendSourceAdapter):
    """Merge signals from multiple trend sources with deduplication.

    Parameters
    ----------
    adapters:
        List of ``(adapter, weight)`` pairs.  A weight of ``2.0`` makes
        that adapter's signals score twice as high after merging.
    cache_ttl:
        TTL in seconds for the merged result cache.  ``0`` disables cache.
    seed:
        Seed for the synthetic fallback source.

    Complexity
    ----------
    fetch(): O(N log N) where N = total signals across all adapters.

    Examples
    --------
    >>> from modules.adapters.synthetic import SyntheticTrendSource
    >>> src = CompositeTrendSource(
    ...     adapters=[(SyntheticTrendSource(seed=0), 1.0),
    ...               (SyntheticTrendSource(seed=1), 1.5)]
    ... )
    >>> signals = src.fetch()
    >>> assert signals == sorted(signals, key=lambda s: s.raw_score, reverse=True)
    """

    _CACHE_KEY = "composite_trends"

    def __init__(
        self,
        adapters: list[tuple[TrendSourceAdapter, float]] | None = None,
        cache_ttl: float = _CACHE_TTL,
        seed: int = 42,
    ) -> None:
        self._adapters = adapters or [(SyntheticTrendSource(seed=seed), 1.0)]
        self._cache: TrendCache[list[TrendSignal]] | None = (
            TrendCache(ttl_seconds=cache_ttl) if cache_ttl > 0 else None
        )
        self._fallback = SyntheticTrendSource(seed=seed)

    # ------------------------------------------------------------------
    # TrendSourceAdapter
    # ------------------------------------------------------------------

    def fetch(self) -> list[TrendSignal]:
        """Return merged, deduplicated, and sorted list of TrendSignals.

        Cached for ``cache_ttl`` seconds to reduce API calls.

        Complexity: O(N log N)
        """
        if self._cache is not None:
            cached = self._cache.get(self._CACHE_KEY)
            if cached is not None:
                logger.debug("CompositeTrendSource: returning %d cached signals", len(cached))
                return cached

        signals = self._merge_all()

        if self._cache is not None:
            self._cache.put(self._CACHE_KEY, signals)

        return signals

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _merge_all(self) -> list[TrendSignal]:
        """Collect, weight, deduplicate, and sort all signals."""
        all_signals: list[TrendSignal] = []

        for adapter, weight in self._adapters:
            try:
                raw = adapter.fetch()                # O(n_i)
                weighted = self._apply_weight(raw, weight)
                all_signals.extend(weighted)
                logger.debug(
                    "%s returned %d signals (weight=%.1f)",
                    type(adapter).__name__, len(raw), weight,
                )
            except Exception as exc:               # noqa: BLE001
                logger.warning("%s failed: %s", type(adapter).__name__, exc)

        if not all_signals:
            logger.warning(
                "All adapters failed; falling back to SyntheticTrendSource"
            )
            return self._fallback.fetch()

        deduped = self._deduplicate(all_signals)    # O(N)
        sorted_signals = sorted(                    # O(N log N)
            deduped, key=lambda s: s.raw_score, reverse=True
        )
        logger.info(
            "CompositeTrendSource: merged %d → %d unique signals",
            len(all_signals), len(sorted_signals),
        )
        return sorted_signals

    @staticmethod
    def _apply_weight(
        signals: list[TrendSignal], weight: float
    ) -> list[TrendSignal]:
        """Multiply raw_score by weight, clamping to [0.0, 1.0].

        Complexity: O(n)
        """
        if weight == 1.0:
            return signals  # no copy needed

        return [
            TrendSignal(
                trend_id=s.trend_id,
                keyword=s.keyword,
                raw_score=min(s.raw_score * weight, 1.0),
                source=s.source,
                timestamp=s.timestamp,
            )
            for s in signals
        ]

    @staticmethod
    def _deduplicate(signals: list[TrendSignal]) -> list[TrendSignal]:
        """Keep the highest-scoring signal per normalised keyword.

        Normalisation: ``keyword.lower().strip()``.
        Complexity: O(n)
        """
        best: dict[str, TrendSignal] = {}

        for signal in signals:
            key = signal.keyword.lower().strip()
            if key not in best or signal.raw_score > best[key].raw_score:
                best[key] = signal

        return list(best.values())
