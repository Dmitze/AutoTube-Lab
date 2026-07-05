"""Tests for MetricsRegistry (T-461, T-462, EPIC 7.2)."""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# T-461: MetricsRegistry increments counters
# ---------------------------------------------------------------------------

def test_metrics_registry_record_run_ok():
    """T-461: record_run('ok') increments the ok counter."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    registry = MetricsRegistry()
    registry.record_run("ok")
    assert registry._run_counts.get("ok", 0) >= 1


def test_metrics_registry_record_run_error():
    """T-461: record_run('error') increments the error counter."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    registry = MetricsRegistry()
    registry.record_run("error")
    assert registry._run_counts.get("error", 0) >= 1


def test_metrics_registry_observe_duration():
    """T-461: observe_duration() records pipeline execution time."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    registry = MetricsRegistry()
    registry.observe_duration(42.5)
    assert len(registry._durations) >= 1
    assert 42.5 in registry._durations


# ---------------------------------------------------------------------------
# T-462: pipeline error → publish error counter incremented
# ---------------------------------------------------------------------------

def test_metrics_registry_record_publish_error():
    """T-462: record_publish_error('compliance') increments error counter."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    registry = MetricsRegistry()
    registry.record_publish_error("compliance")
    assert registry._publish_errors.get("compliance", 0) >= 1


def test_metrics_registry_multiple_runs():
    """T-461: Multiple runs are counted correctly."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    registry = MetricsRegistry()
    for _ in range(5):
        registry.record_run("ok")
    for _ in range(2):
        registry.record_run("error")
    assert registry._run_counts["ok"] == 5
    assert registry._run_counts["error"] == 2


def test_metrics_registry_summary():
    """T-461: summary() returns dict with all metric categories."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    registry = MetricsRegistry()
    registry.record_run("ok")
    registry.observe_duration(10.0)
    registry.record_publish_error("quota")

    summary = registry.summary()
    assert "runs" in summary
    assert "durations" in summary
    assert "publish_errors" in summary
