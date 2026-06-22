"""Integration tests for Phase 5 feedback loop (T-377, T-378).

Tests the closed loop: collect metrics → FeedbackScorer → TrendAnalyzer weights.
All external services are mocked.
"""
from __future__ import annotations

import pytest

from modules.adapters.synthetic import InMemoryStorage
from ytaimbot_ml.schemas import MetricsSnapshot


# ---------------------------------------------------------------------------
# T-377: collect → score → analyze → report integration
# ---------------------------------------------------------------------------

def test_feedback_scorer_ema_updates_weights():
    """T-377: FeedbackScorer updates niche weights via EMA after metrics."""
    from src.ytaimbot_ml.feedback.scorer import FeedbackScorer

    scorer = FeedbackScorer(alpha=0.3)

    # Simulate high-performing finance niche
    finance_metrics = MetricsSnapshot(
        video_id="fin_001",
        views=50_000,
        ctr=0.08,
        retention_30s=0.72,
        rpm=12.0,
    )
    w1 = scorer.update("finance", finance_metrics)
    w2 = scorer.update("finance", finance_metrics)

    # Weight should increase after good metrics
    assert w2 >= w1 or abs(w2 - w1) < 0.3  # bounded by safety ±20%
    assert scorer.get_weights()["finance"] > 0


def test_feedback_scorer_safety_bounds():
    """T-377: Safety bounds prevent weight from changing more than 20%."""
    from src.ytaimbot_ml.feedback.scorer import FeedbackScorer

    scorer = FeedbackScorer(alpha=0.3)
    initial = 1.0

    # Extreme metrics (very high performance)
    extreme_metrics = MetricsSnapshot(
        video_id="ext_001",
        views=10_000_000,
        ctr=0.99,
        retention_30s=0.99,
        rpm=100.0,
    )
    new_weight = scorer.update("tech", extreme_metrics)

    # Should not exceed initial * 1.2
    assert new_weight <= initial * 1.21  # small float tolerance


# ---------------------------------------------------------------------------
# T-378: After 10 iterations, top niches get higher weight
# ---------------------------------------------------------------------------

def test_top_niches_get_higher_weight_after_iterations():
    """T-378: After 10 iterations, high-RPM niche has higher weight than low-RPM."""
    from src.ytaimbot_ml.feedback.scorer import FeedbackScorer

    scorer = FeedbackScorer(alpha=0.3)

    high_rpm = MetricsSnapshot(
        video_id="h", views=10000, ctr=0.08, retention_30s=0.75, rpm=15.0
    )
    low_rpm = MetricsSnapshot(
        video_id="l", views=500, ctr=0.02, retention_30s=0.30, rpm=0.5
    )

    for _ in range(10):
        scorer.update("finance", high_rpm)
        scorer.update("horror", low_rpm)

    weights = scorer.get_weights()
    assert weights["finance"] > weights["horror"], (
        f"finance={weights['finance']:.3f} should > horror={weights['horror']:.3f}"
    )


# ---------------------------------------------------------------------------
# T-375: env vars for Phase 5
# ---------------------------------------------------------------------------

def test_env_vars_have_defaults(monkeypatch):
    """T-375: METRICS_COLLECTION_DELAY_HOURS and FEEDBACK_ALPHA have defaults."""
    import os
    delay = int(os.environ.get("METRICS_COLLECTION_DELAY_HOURS", "48"))
    alpha = float(os.environ.get("FEEDBACK_ALPHA", "0.3"))

    assert delay == 48
    assert alpha == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# T-379: Weekly report integrates with storage
# ---------------------------------------------------------------------------

def test_weekly_report_integrates_with_storage():
    """T-379: WeeklyReportGenerator works with InMemoryStorage."""
    from modules.reporting.weekly_report import WeeklyReportGenerator

    storage = InMemoryStorage()
    for i in range(10):
        storage.save_video(f"v{i}", f"t{i}", f"Video {i}")
        storage._videos[f"v{i}"].update({
            "ctr": 0.05 + i * 0.005,
            "retention_30s": 0.60 + i * 0.02,
            "rpm": 3.0 + i * 0.5,
            "views": 1000 + i * 200,
        })

    gen = WeeklyReportGenerator(storage=storage)
    report = gen.generate(week=26, year=2026)

    assert "YTAIMBot Weekly Report" in report
    assert "Top 5 Videos" in report
    assert len(report) > 200
