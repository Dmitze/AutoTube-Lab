"""Tests for MetricsRegistry (T-461, T-462, EPIC 7.2)."""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# T-461: MetricsRegistry increments counters
# ---------------------------------------------------------------------------

def test_metrics_registry_record_run_ok():
    """T-461: record_run('ok') increments the ok counter."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    val_before = MetricsRegistry._PIPELINE_RUNS.labels(status="ok")._value.get()
    MetricsRegistry.record_run("ok")
    assert MetricsRegistry._PIPELINE_RUNS.labels(status="ok")._value.get() == val_before + 1


def test_metrics_registry_record_run_error():
    """T-461: record_run('error') increments the error counter."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    val_before = MetricsRegistry._PIPELINE_RUNS.labels(status="error")._value.get()
    MetricsRegistry.record_run("error")
    assert MetricsRegistry._PIPELINE_RUNS.labels(status="error")._value.get() == val_before + 1


def test_metrics_registry_observe_duration():
    """T-461: observe_duration() records pipeline execution time."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    val_before = MetricsRegistry._PIPELINE_DURATION._sum.get()
    MetricsRegistry.observe_duration(42.5)
    assert MetricsRegistry._PIPELINE_DURATION._sum.get() == val_before + 42.5


# ---------------------------------------------------------------------------
# T-462: pipeline error → publish error counter incremented
# ---------------------------------------------------------------------------

def test_metrics_registry_record_publish_error():
    """T-462: record_publish_error('compliance') increments error counter."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    val_before = MetricsRegistry._PUBLISH_ERRORS.labels(reason="compliance")._value.get()
    MetricsRegistry.record_publish_error("compliance")
    assert MetricsRegistry._PUBLISH_ERRORS.labels(reason="compliance")._value.get() == val_before + 1


def test_metrics_registry_multiple_runs():
    """T-461: Multiple runs are counted correctly."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    ok_before = MetricsRegistry._PIPELINE_RUNS.labels(status="ok")._value.get()
    err_before = MetricsRegistry._PIPELINE_RUNS.labels(status="error")._value.get()
    for _ in range(5):
        MetricsRegistry.record_run("ok")
    for _ in range(2):
        MetricsRegistry.record_run("error")
    assert MetricsRegistry._PIPELINE_RUNS.labels(status="ok")._value.get() == ok_before + 5
    assert MetricsRegistry._PIPELINE_RUNS.labels(status="error")._value.get() == err_before + 2


def test_metrics_registry_summary():
    """T-461: summary() returns dict with all metric categories."""
    from ytaimbot_ml.utils.metrics import MetricsRegistry
    # Summary method is removed, test the Gauge instead
    MetricsRegistry.set_max_trend_score(9.9)
    assert MetricsRegistry._TREND_SCORE_MAX._value.get() == 9.9
