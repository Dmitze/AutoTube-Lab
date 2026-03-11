"""Tests for CompositeTrendSource — T-056 to T-060."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from modules.adapters.composite import CompositeTrendSource
from ytaimbot_ml.schemas import TrendSignal


def _signal(keyword: str, score: float, source: str = "test") -> TrendSignal:
    return TrendSignal(
        trend_id=f"t_{keyword}",
        keyword=keyword,
        raw_score=score,
        source=source,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _adapter(signals: list[TrendSignal]) -> MagicMock:
    m = MagicMock()
    m.fetch.return_value = signals
    return m


# ---------------------------------------------------------------------------
# Merge + sort
# ---------------------------------------------------------------------------

def test_fetch_returns_sorted_signals():
    """Merged result must be sorted descending by raw_score."""
    a1 = _adapter([_signal("python", 0.3), _signal("rust", 0.9)])
    a2 = _adapter([_signal("go", 0.6)])

    src = CompositeTrendSource(adapters=[(a1, 1.0), (a2, 1.0)], cache_ttl=0)
    signals = src.fetch()

    scores = [s.raw_score for s in signals]
    assert scores == sorted(scores, reverse=True)


def test_deduplication_keeps_higher_score():
    """Duplicate keyword → keep the one with higher raw_score."""
    a1 = _adapter([_signal("python", 0.5)])
    a2 = _adapter([_signal("Python", 0.9)])   # same keyword, different case

    src = CompositeTrendSource(adapters=[(a1, 1.0), (a2, 1.0)], cache_ttl=0)
    signals = src.fetch()

    keywords = [s.keyword.lower() for s in signals]
    assert keywords.count("python") == 1
    match = next(s for s in signals if s.keyword.lower() == "python")
    assert match.raw_score == pytest.approx(0.9)


def test_weight_multiplier_increases_score():
    """Weight > 1.0 boosts score (capped at 1.0)."""
    a = _adapter([_signal("go", 0.4)])
    src = CompositeTrendSource(adapters=[(a, 2.0)], cache_ttl=0)
    signals = src.fetch()

    # 0.4 × 2.0 = 0.8 (within range)
    assert signals[0].raw_score == pytest.approx(0.8)


def test_weight_clamped_at_one():
    """Weighted score must not exceed 1.0."""
    a = _adapter([_signal("hot", 0.9)])
    src = CompositeTrendSource(adapters=[(a, 3.0)], cache_ttl=0)
    signals = src.fetch()

    assert signals[0].raw_score <= 1.0


def test_failing_adapter_does_not_block_others():
    """If one adapter raises, others must still contribute."""
    bad = MagicMock()
    bad.fetch.side_effect = RuntimeError("network error")
    good = _adapter([_signal("java", 0.7)])

    src = CompositeTrendSource(adapters=[(bad, 1.0), (good, 1.0)], cache_ttl=0)
    signals = src.fetch()

    assert len(signals) >= 1
    assert any(s.keyword == "java" for s in signals)


def test_all_adapters_fail_returns_synthetic():
    """When all adapters fail, fallback to SyntheticTrendSource."""
    bad1 = MagicMock()
    bad1.fetch.side_effect = RuntimeError("err1")
    bad2 = MagicMock()
    bad2.fetch.side_effect = RuntimeError("err2")

    src = CompositeTrendSource(
        adapters=[(bad1, 1.0), (bad2, 1.0)], cache_ttl=0, seed=42
    )
    signals = src.fetch()

    assert isinstance(signals, list)
    assert len(signals) >= 1
    assert all(isinstance(s, TrendSignal) for s in signals)


def test_cache_hit_avoids_second_fetch():
    """Second call within TTL must not call adapters again."""
    a = _adapter([_signal("cached", 0.5)])
    src = CompositeTrendSource(adapters=[(a, 1.0)], cache_ttl=60)

    src.fetch()
    src.fetch()  # should hit cache

    assert a.fetch.call_count == 1
