"""Unit tests for TrendAnalyzer."""

from __future__ import annotations

import numpy as np
import pytest

from ytaimbot_ml.trend_analyzer import TrendAnalyzer
from ytaimbot_ml.schemas import TrendSignal
from ytaimbot_ml.utils.random import make_rng


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_signals(n: int, seed: int = 0) -> list[TrendSignal]:
    rng = np.random.default_rng(seed)
    scores = rng.uniform(0.1, 1.0, size=n)
    return [
        TrendSignal(
            trend_id=f"t{i:03d}",
            keyword=f"keyword_{i}",
            raw_score=float(scores[i]),
            source="test",
            timestamp="2026-01-01T00:00:00Z",
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_pca_reduces_dimensions(sample_features_matrix: np.ndarray) -> None:
    """fit_transform should reduce the second dimension to n_components."""
    analyzer = TrendAnalyzer(rng=make_rng(42))
    n_components = 2
    reduced = analyzer.fit_transform(sample_features_matrix, n_components)
    assert reduced.shape == (sample_features_matrix.shape[0], n_components)


def test_scoring_returns_sorted(synthetic_trends: list[TrendSignal]) -> None:
    """score_trends should return rankings in descending score order."""
    analyzer = TrendAnalyzer(rng=make_rng(42))
    feature_matrix = np.random.default_rng(0).uniform(0, 1, size=(len(synthetic_trends), 3))
    trend_ids = [s.trend_id for s in synthetic_trends]
    rankings = analyzer.score_trends(feature_matrix, trend_ids)

    scores = [r.score for r in rankings]
    assert scores == sorted(scores, reverse=True), "Rankings must be sorted descending"


def test_determinism(synthetic_trends: list[TrendSignal]) -> None:
    """Two TrendAnalyzer calls with the same seed must produce identical results."""
    analyzer_a = TrendAnalyzer(rng=make_rng(99))
    analyzer_b = TrendAnalyzer(rng=make_rng(99))

    rankings_a = analyzer_a.analyze(synthetic_trends)
    rankings_b = analyzer_b.analyze(synthetic_trends)

    assert [r.trend_id for r in rankings_a] == [r.trend_id for r in rankings_b]
    assert [r.score for r in rankings_a] == pytest.approx(
        [r.score for r in rankings_b], rel=1e-9
    )


def test_top5_overlap(synthetic_trends: list[TrendSignal]) -> None:
    """The top-5 trends from two different seeds should overlap >= 80 %."""
    rankings_a = TrendAnalyzer(rng=make_rng(1)).analyze(synthetic_trends)
    rankings_b = TrendAnalyzer(rng=make_rng(2)).analyze(synthetic_trends)

    top5_a = {r.trend_id for r in rankings_a[:5]}
    top5_b = {r.trend_id for r in rankings_b[:5]}
    overlap = len(top5_a & top5_b) / 5.0
    assert overlap >= 0.8, f"Top-5 overlap is {overlap:.0%}, expected >= 80%"


def test_analyze_empty_signals() -> None:
    """analyze([]) should return an empty list without raising."""
    analyzer = TrendAnalyzer(rng=make_rng(0))
    assert analyzer.analyze([]) == []


def test_analyze_single_signal() -> None:
    """analyze with a single signal should return a ranking without error."""
    analyzer = TrendAnalyzer(rng=make_rng(0))
    sig = TrendSignal(
        trend_id="only",
        keyword="solo",
        raw_score=0.5,
        source="test",
        timestamp="2026-01-01T00:00:00Z",
    )
    rankings = analyzer.analyze([sig])
    assert len(rankings) == 1
    assert rankings[0].trend_id == "only"
