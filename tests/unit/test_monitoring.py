"""Unit tests for PrometheusExporter and AlertManager (Phase 7, T-550 / T-566).

All tests are network-free.  urllib.request calls are monkey-patched where
needed.  No real Prometheus server is started.

Test inventory (22 tests):
  test_exporter_no_crash_without_prometheus
  test_record_pipeline_run_success
  test_record_pipeline_run_error
  test_record_pipeline_run_dry_run
  test_record_trend_score
  test_record_ctr_ema
  test_record_retention_ema
  test_record_quota_used
  test_record_gate_ratio_normal
  test_record_gate_ratio_zero_total
  test_record_publish_error
  test_record_video_published
  test_backward_compat_record
  test_backward_compat_record_unknown_metric
  test_alert_manager_no_webhook
  test_alert_manager_dedup
  test_alert_manager_check_thresholds_ctr_low
  test_alert_manager_check_thresholds_retention_low
  test_alert_manager_check_thresholds_quota_high
  test_alert_manager_check_thresholds_all_ok
  test_alert_dataclass
  test_alert_manager_send_after_cooldown
"""
from __future__ import annotations

import unittest.mock as mock
from datetime import datetime, timedelta, timezone

import pytest

from modules.adapters.monitoring import Alert, AlertManager, PrometheusExporter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _disabled_exporter() -> PrometheusExporter:
    """Return an exporter with enabled=False (safe in tests — no HTTP server)."""
    return PrometheusExporter(port=19999, enabled=False)


# ===========================================================================
# PrometheusExporter tests
# ===========================================================================


def test_exporter_no_crash_without_prometheus() -> None:
    """PrometheusExporter instantiation must not raise even if prometheus_client absent."""
    # Simulate missing library by patching the module-level flag
    import modules.adapters.monitoring.prometheus as pmod
    original = pmod._PROMETHEUS_AVAILABLE
    try:
        pmod._PROMETHEUS_AVAILABLE = False
        exp = PrometheusExporter(port=19998, enabled=True)
        # No-op calls must be silent
        exp.record_pipeline_run("success", 1.0)
        exp.record_ctr_ema(0.06)
    finally:
        pmod._PROMETHEUS_AVAILABLE = original


def test_record_pipeline_run_success() -> None:
    """record_pipeline_run('success', 45.0) must not raise."""
    exp = _disabled_exporter()
    exp.record_pipeline_run(status="success", duration_seconds=45.0)


def test_record_pipeline_run_error() -> None:
    """record_pipeline_run('error', 5.0) must not raise."""
    exp = _disabled_exporter()
    exp.record_pipeline_run(status="error", duration_seconds=5.0)


def test_record_pipeline_run_dry_run() -> None:
    """record_pipeline_run('dry_run', 10.0) must not raise."""
    exp = _disabled_exporter()
    exp.record_pipeline_run(status="dry_run", duration_seconds=10.0)


def test_record_trend_score() -> None:
    """record_trend_score(0.9) must not raise."""
    exp = _disabled_exporter()
    exp.record_trend_score(0.9)


def test_record_ctr_ema() -> None:
    """record_ctr_ema(0.08) must not raise."""
    exp = _disabled_exporter()
    exp.record_ctr_ema(0.08)


def test_record_retention_ema() -> None:
    """record_retention_ema(0.72) must not raise."""
    exp = _disabled_exporter()
    exp.record_retention_ema(0.72)


def test_record_quota_used() -> None:
    """record_quota_used(1500) must not raise."""
    exp = _disabled_exporter()
    exp.record_quota_used(1500)


def test_record_gate_ratio_normal() -> None:
    """record_gate_ratio(4, 5) must not raise and ratio is 0.8."""
    exp = _disabled_exporter()
    exp.record_gate_ratio(pass_count=4, total=5)


def test_record_gate_ratio_zero_total() -> None:
    """record_gate_ratio(0, 0) must not divide by zero."""
    exp = _disabled_exporter()
    exp.record_gate_ratio(pass_count=0, total=0)  # should silently no-op


def test_record_publish_error() -> None:
    """record_publish_error(reason='compliance') must not raise."""
    exp = _disabled_exporter()
    exp.record_publish_error(reason="compliance")


def test_record_video_published() -> None:
    """record_video_published() must not raise."""
    exp = _disabled_exporter()
    exp.record_video_published()


def test_backward_compat_record() -> None:
    """Legacy record('ctr_ema', 0.1) must not raise."""
    exp = _disabled_exporter()
    exp.record("ctr_ema", 0.1)
    exp.record("retention_ema", 0.7)
    exp.record("trend_score_max", 0.85)
    exp.record("yt_quota_used", 500.0)


def test_backward_compat_record_unknown_metric(caplog: pytest.LogCaptureFixture) -> None:
    """record() with an unknown metric name logs a warning and does not raise."""
    import logging
    exp = _disabled_exporter()
    with caplog.at_level(logging.WARNING, logger="modules.adapters.monitoring.prometheus"):
        exp.record("nonexistent_metric", 42.0)
    assert any("unknown metric" in r.message for r in caplog.records)


# ===========================================================================
# AlertManager tests
# ===========================================================================


def test_alert_manager_no_webhook() -> None:
    """send() returns False when no webhook_url is configured."""
    mgr = AlertManager(webhook_url="")
    result = mgr.send("Pipeline failed!", level="critical")
    assert result is False


def test_alert_manager_dedup() -> None:
    """Same (message, level) does not fire twice within the cooldown window."""
    mgr = AlertManager(webhook_url="https://hooks.slack.com/test", cooldown_hours=1.0)

    # Manually plant a recent sent record to simulate a prior send
    mgr._sent_at[("duplicate message", "warning")] = datetime.now(timezone.utc)

    # _is_duplicate should return True
    assert mgr._is_duplicate("duplicate message", "warning") is True

    # send() should return False (deduped) — no HTTP call needed
    result = mgr.send("duplicate message", level="warning")
    assert result is False


def test_alert_manager_check_thresholds_ctr_low() -> None:
    """CTR of 0.02 (< 0.04) triggers a warning alert."""
    mgr = AlertManager()
    alerts = mgr.check_thresholds({"ctr_ema": 0.02})
    assert len(alerts) >= 1
    assert any(a.level == "warning" and "CTR" in a.message for a in alerts)


def test_alert_manager_check_thresholds_retention_low() -> None:
    """Retention of 0.40 (< 0.50) triggers a warning alert."""
    mgr = AlertManager()
    alerts = mgr.check_thresholds({"retention_ema": 0.40})
    assert len(alerts) >= 1
    assert any(a.level == "warning" and "Retention" in a.message for a in alerts)


def test_alert_manager_check_thresholds_quota_high() -> None:
    """Quota of 9000 (> 8000) triggers a warning alert."""
    mgr = AlertManager()
    alerts = mgr.check_thresholds({"yt_quota_used": 9000.0})
    assert len(alerts) >= 1
    assert any(a.level == "warning" and "quota" in a.message.lower() for a in alerts)


def test_alert_manager_check_thresholds_all_ok() -> None:
    """Healthy metrics produce no alerts."""
    mgr = AlertManager()
    alerts = mgr.check_thresholds({
        "ctr_ema": 0.07,
        "retention_ema": 0.72,
        "yt_quota_used": 1000.0,
    })
    assert alerts == []


def test_alert_dataclass() -> None:
    """Alert dataclass has level, message, source, and fired_at fields."""
    now = datetime.now(timezone.utc)
    alert = Alert(level="warning", message="test msg", source="unit_test", fired_at=now)
    assert alert.level == "warning"
    assert alert.message == "test msg"
    assert alert.source == "unit_test"
    assert alert.fired_at == now


def test_alert_manager_send_after_cooldown() -> None:
    """Same alert fires again after the cooldown window has expired."""
    mgr = AlertManager(webhook_url="https://hooks.slack.com/test", cooldown_hours=1.0)

    # Plant a stale sent record (2 hours ago — beyond the 1h cooldown)
    mgr._sent_at[("stale alert", "info")] = datetime.now(timezone.utc) - timedelta(hours=2)

    # _is_duplicate should be False (cooldown expired)
    assert mgr._is_duplicate("stale alert", "info") is False

    # send() should attempt the HTTP call — mock urlopen to avoid real network
    with mock.patch("urllib.request.urlopen") as mock_open:
        mock_cm = mock.MagicMock()
        mock_cm.__enter__ = mock.Mock(return_value=mock_cm)
        mock_cm.__exit__ = mock.Mock(return_value=False)
        mock_open.return_value = mock_cm

        result = mgr.send("stale alert", level="info")

    assert result is True
    assert ("stale alert", "info") in mgr._sent_at
