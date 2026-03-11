"""Phase 7 — Monitoring adapters sub-package.

Adapters
--------
PrometheusExporter : exposes metrics on :8000/metrics
AlertManager       : threshold-based Slack/webhook alerts
Alert              : immutable alert event dataclass

Metrics exported:
  ytaimbot_pipeline_runs_total         Counter  (label: status)
  ytaimbot_pipeline_duration_seconds   Histogram
  ytaimbot_publish_errors_total        Counter  (label: reason)
  ytaimbot_trend_score_max             Gauge
  ytaimbot_ctr_ema                     Gauge    (target ≥ 0.06)
  ytaimbot_retention_ema               Gauge    (target ≥ 0.70)
  ytaimbot_yt_quota_used               Gauge    (max 10000/day)
  ytaimbot_gate_pass_ratio             Gauge
  ytaimbot_videos_published_total      Counter
"""
from __future__ import annotations

from modules.adapters.monitoring.alerts import Alert, AlertManager
from modules.adapters.monitoring.prometheus import PrometheusExporter

__all__ = ["PrometheusExporter", "AlertManager", "Alert"]
