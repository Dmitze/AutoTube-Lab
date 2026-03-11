"""Phase 7 — Monitoring adapters sub-package.

Adapters
--------
PrometheusExporter : exposes metrics on :8000/metrics
AlertManager       : threshold-based Slack/webhook alerts

Metrics exported:
  ytaimbot_videos_published_total   Counter
  ytaimbot_pipeline_duration_seconds Histogram
  ytaimbot_ctr_ema                  Gauge (target ≥ 0.06)
  ytaimbot_retention_ema            Gauge (target ≥ 0.70)
  ytaimbot_yt_quota_used            Gauge (max 10000/day)
  ytaimbot_gate_pass_ratio          Gauge

Status: 🔲 Pending — T-550 (Phase 7, EPIC 7.2)
"""
