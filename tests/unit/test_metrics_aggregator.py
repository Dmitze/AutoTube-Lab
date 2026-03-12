"""Unit tests for MetricsAggregator."""
from __future__ import annotations

import pytest

from ytaimbot_ml.metrics.aggregator import MetricsAggregator
from ytaimbot_ml.schemas import PipelineResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(run_id: str = "r1", status: str = "ok") -> PipelineResult:
    return PipelineResult(run_id=run_id, status=status)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_get_window_stats_empty():
    agg = MetricsAggregator(window_size=10)
    stats = agg.get_window_stats()
    assert stats["total_runs"] == 0.0
    assert stats["success_rate"] == 0.0
    assert stats["error_rate"] == 0.0
    assert stats["dry_run_rate"] == 0.0
    assert stats["avg_ctr"] == 0.0
    assert stats["avg_retention"] == 0.0


# ---------------------------------------------------------------------------
# record_pipeline_run
# ---------------------------------------------------------------------------


def test_record_single_run():
    agg = MetricsAggregator(window_size=10)
    agg.record_pipeline_run(_make_result("r1", "ok"))
    assert agg.get_window_stats()["total_runs"] == 1.0


def test_record_without_exporter():
    """Should not raise even when no exporter is configured."""
    agg = MetricsAggregator(window_size=5, exporter=None)
    agg.record_pipeline_run(_make_result("r1", "ok"))
    assert agg.get_window_stats()["total_runs"] == 1.0


def test_record_published_status():
    agg = MetricsAggregator(window_size=5)
    agg.record_pipeline_run(_make_result("r1", "published"))
    stats = agg.get_window_stats()
    assert stats["total_runs"] == 1.0
    assert stats["success_rate"] == 1.0


def test_record_error_status():
    agg = MetricsAggregator(window_size=5)
    agg.record_pipeline_run(_make_result("r1", "error"))
    stats = agg.get_window_stats()
    assert stats["error_rate"] == 1.0
    assert stats["success_rate"] == 0.0


def test_record_dry_run_status():
    agg = MetricsAggregator(window_size=5)
    agg.record_pipeline_run(_make_result("r1", "dry_run"))
    stats = agg.get_window_stats()
    assert stats["dry_run_rate"] == 1.0
    assert stats["success_rate"] == 0.0
    assert stats["error_rate"] == 0.0


# ---------------------------------------------------------------------------
# Window statistics
# ---------------------------------------------------------------------------


def test_window_stats_total_runs():
    agg = MetricsAggregator(window_size=20)
    for i in range(5):
        agg.record_pipeline_run(_make_result(f"r{i}", "ok"))
    assert agg.get_window_stats()["total_runs"] == 5.0


def test_window_stats_success_rate():
    agg = MetricsAggregator(window_size=10)
    for i in range(3):
        agg.record_pipeline_run(_make_result(f"ok{i}", "ok"))
    for i in range(1):
        agg.record_pipeline_run(_make_result(f"err{i}", "error"))
    stats = agg.get_window_stats()
    assert stats["success_rate"] == pytest.approx(0.75)
    assert stats["error_rate"] == pytest.approx(0.25)


def test_window_stats_error_rate():
    agg = MetricsAggregator(window_size=10)
    agg.record_pipeline_run(_make_result("e1", "error"))
    agg.record_pipeline_run(_make_result("e2", "error"))
    agg.record_pipeline_run(_make_result("o1", "ok"))
    stats = agg.get_window_stats()
    assert stats["error_rate"] == pytest.approx(2 / 3)


def test_window_size_limit():
    """Window must not grow beyond window_size."""
    agg = MetricsAggregator(window_size=3)
    for i in range(10):
        agg.record_pipeline_run(_make_result(f"r{i}", "ok"))
    assert agg.get_window_stats()["total_runs"] == 3.0


def test_window_stats_avg_ctr():
    """avg_ctr key must be present and be a float."""
    agg = MetricsAggregator(window_size=10)
    agg.record_pipeline_run(_make_result("r1", "ok"))
    stats = agg.get_window_stats()
    assert "avg_ctr" in stats
    assert isinstance(stats["avg_ctr"], float)


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


def test_reset_clears_window():
    agg = MetricsAggregator(window_size=10)
    for i in range(5):
        agg.record_pipeline_run(_make_result(f"r{i}", "ok"))
    agg.reset()
    stats = agg.get_window_stats()
    assert stats["total_runs"] == 0.0
    assert stats["success_rate"] == 0.0
    assert stats["avg_ctr"] == 0.0


# ===========================================================================
# EMATracker (aggregator module: alpha in (0, 1], always-apply formula)
# ===========================================================================

from ytaimbot_ml.metrics import EMATracker, PipelineMetrics  # noqa: E402


def test_ema_tracker_initial() -> None:
    """Default initial value is 0.0 before any updates."""
    ema = EMATracker(alpha=0.3, initial=0.0)
    assert ema.value == 0.0
    assert ema.count == 0


def test_ema_tracker_update() -> None:
    """update() applies EMA formula: alpha * value + (1 - alpha) * prev."""
    ema = EMATracker(alpha=0.3, initial=0.0)
    ema.update(10.0)
    # 0.3 * 10.0 + 0.7 * 0.0 = 3.0
    assert 2.5 < ema.value < 4.0
    assert ema.count == 1


def test_ema_tracker_alpha_one_is_last_value() -> None:
    """alpha=1.0 means EMA always equals the most recent value."""
    ema = EMATracker(alpha=1.0, initial=99.0)
    ema.update(5.0)
    assert ema.value == pytest.approx(5.0)
    ema.update(42.0)
    assert ema.value == pytest.approx(42.0)


def test_ema_invalid_alpha_raises() -> None:
    """Alpha outside (0, 1] raises ValueError."""
    with pytest.raises(ValueError):
        EMATracker(alpha=0.0)
    with pytest.raises(ValueError):
        EMATracker(alpha=-0.5)
    with pytest.raises(ValueError):
        EMATracker(alpha=1.1)


# ===========================================================================
# PipelineMetrics
# ===========================================================================


def test_pipeline_metrics_empty() -> None:
    """PipelineMetrics.empty() returns all-zero snapshot with a timestamp."""
    snap = PipelineMetrics.empty()
    assert snap.videos_published == 0
    assert snap.avg_ctr == 0.0
    assert snap.avg_retention_30s == 0.0
    assert snap.quota_used == 0
    assert snap.error_count == 0
    assert snap.revenue_estimate == 0.0
    assert isinstance(snap.timestamp, str)
    assert len(snap.timestamp) > 0


# ===========================================================================
# MetricsAggregator — video-publish interface (T-416 extension)
# ===========================================================================


def test_aggregator_initial_snapshot_zeros() -> None:
    """Fresh aggregator snapshot has all-zero video counters."""
    agg = MetricsAggregator()
    snap = agg.snapshot()
    assert snap.videos_published == 0
    assert snap.avg_ctr == 0.0
    assert snap.avg_retention_30s == 0.0
    assert snap.quota_used == 0
    assert snap.error_count == 0
    assert snap.revenue_estimate == 0.0


def test_aggregator_record_video_published() -> None:
    """record_video_published increments videos_published counter."""
    agg = MetricsAggregator()
    agg.record_video_published(ctr=0.08, retention=0.72, revenue=1.5)
    agg.record_video_published(ctr=0.07, retention=0.65, revenue=1.0)
    snap = agg.snapshot()
    assert snap.videos_published == 2


def test_aggregator_record_error() -> None:
    """record_error increments error_count in snapshot."""
    agg = MetricsAggregator()
    agg.record_error("bayes_filter")
    agg.record_error("publish_failed")
    snap = agg.snapshot()
    assert snap.error_count == 2


def test_aggregator_record_quota_usage() -> None:
    """record_quota_usage accumulates into quota_used."""
    agg = MetricsAggregator()
    agg.record_quota_usage(50)
    agg.record_quota_usage(25)
    snap = agg.snapshot()
    assert snap.quota_used == 75


def test_aggregator_snapshot_ctr() -> None:
    """snapshot().avg_ctr reflects the CTR after first publish (direct set)."""
    agg = MetricsAggregator()
    agg.record_video_published(ctr=0.10, retention=0.70)
    snap = agg.snapshot()
    assert 0.09 < snap.avg_ctr < 0.11


def test_aggregator_snapshot_retention() -> None:
    """snapshot().avg_retention_30s reflects the last retention value."""
    agg = MetricsAggregator()
    agg.record_video_published(ctr=0.06, retention=0.72)
    snap = agg.snapshot()
    assert 0.70 < snap.avg_retention_30s < 0.74


def test_aggregator_reset() -> None:
    """reset() zeros all video-publish counters and EMA state."""
    agg = MetricsAggregator()
    agg.record_video_published(ctr=0.10, retention=0.70, revenue=2.0)
    agg.record_error("test_error")
    agg.record_quota_usage(100)
    agg.reset()
    snap = agg.snapshot()
    assert snap.videos_published == 0
    assert snap.avg_ctr == 0.0
    assert snap.avg_retention_30s == 0.0
    assert snap.error_count == 0
    assert snap.quota_used == 0
    assert snap.revenue_estimate == 0.0


def test_aggregator_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """from_env() builds MetricsAggregator from METRICS_CTR_ALPHA env vars."""
    monkeypatch.setenv("METRICS_CTR_ALPHA", "0.5")
    monkeypatch.setenv("METRICS_RETENTION_ALPHA", "0.2")
    agg = MetricsAggregator.from_env()
    assert isinstance(agg, MetricsAggregator)
    agg.record_video_published(ctr=0.10, retention=0.60)
    snap = agg.snapshot()
    assert 0.09 < snap.avg_ctr < 0.11
