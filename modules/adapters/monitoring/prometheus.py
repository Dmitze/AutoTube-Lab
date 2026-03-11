"""Phase 7 — PrometheusExporter: exports pipeline metrics for Prometheus scraping.

Roadmap tasks: T-550 through T-565 (EPIC 7.2 Monitoring)
Depends on:   prometheus_client library

Endpoint: http://bot:8000/metrics (scraped every 15s by Prometheus)

Algorithm
---------
Metric types:
  Counter    : monotonically increasing (videos published, errors)
  Gauge      : current value (EMA CTR, retention, quota used)
  Histogram  : distribution (pipeline duration, render time)

  All operations: O(1) update, O(m) scrape where m = metric count

Status: 🔲 Pending — T-550 (Phase 7)
"""
from __future__ import annotations

# TODO: T-550 — implement PrometheusExporter class
# TODO: T-551 — register all metrics at module import
# TODO: T-552 — implement start_server(port=8000) → None
# TODO: T-553 — implement record(metric_name, value) → None


class PrometheusExporter:
    """TODO: implement in T-550."""

    def start_server(self, port: int = 8000) -> None:
        """TODO: T-552."""
        raise NotImplementedError("T-550 pending")

    def record(self, metric_name: str, value: float) -> None:
        """TODO: T-553."""
        raise NotImplementedError("T-550 pending")
