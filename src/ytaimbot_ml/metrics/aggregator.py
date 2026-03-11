"""Phase 5 — MetricsAggregator: collects and exposes pipeline metrics.

Roadmap tasks: T-416 through T-430 (EPIC 5.2 Prometheus Metrics)
Depends on:   prometheus_client, EMATracker

Metrics exposed on :8000/metrics:
  ytaimbot_videos_published_total     Counter
  ytaimbot_pipeline_duration_seconds  Histogram
  ytaimbot_ctr_ema                    Gauge
  ytaimbot_retention_ema              Gauge
  ytaimbot_quota_used_units           Gauge
  ytaimbot_gate_pass_ratio            Gauge

Algorithm
---------
Aggregation: sliding window over last N runs → O(N)
Prometheus scrape: pull model, 15s interval

Status: 🔲 Pending — T-416 (Phase 5)
"""
from __future__ import annotations

# TODO: T-416 — implement MetricsAggregator with prometheus_client
# TODO: T-417 — implement record_pipeline_run(result) → None
# TODO: T-418 — implement start_http_server(port=8000) → None


class MetricsAggregator:
    """TODO: implement in T-416."""

    def record_pipeline_run(self, result) -> None:  # type: ignore[override]
        """TODO: T-417."""
        raise NotImplementedError("T-416 pending")
