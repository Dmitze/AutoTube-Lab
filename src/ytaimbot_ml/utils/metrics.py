"""Phase 7 — MetricsRegistry: custom Prometheus instrumentation (T-454).

Algorithm
---------
1. Counters:
   ytaimbot_pipeline_runs_total (status: success, error, dry_run).
   ytaimbot_publish_errors_total (reason: quota, auth, compliance).

2. Histograms:
   ytaimbot_pipeline_duration_seconds (latency buckets).

3. Gauges:
   ytaimbot_trend_score_max (highest score in last run).

Complexity: O(1) for increments/observations.
"""

from __future__ import annotations

import time
import logging
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, start_http_server

logger = logging.getLogger(__name__)


class MetricsRegistry:
    """Registry for YTAIMBot custom Prometheus metrics."""

    _PIPELINE_RUNS = Counter(
        "ytaimbot_pipeline_runs_total",
        "Total pipeline runs",
        ["status"] # success, error, dry_run
    )
    
    _PIPELINE_DURATION = Histogram(
        "ytaimbot_pipeline_duration_seconds",
        "Pipeline execution time",
        buckets=[30, 60, 120, 300, 600, 1200]
    )
    
    _PUBLISH_ERRORS = Counter(
        "ytaimbot_publish_errors_total",
        "Publishing failures",
        ["reason"] # quota, auth, compliance
    )
    
    _TREND_SCORE_MAX = Gauge(
        "ytaimbot_trend_score_max",
        "Highest trend score in last run"
    )

    @classmethod
    def start_server(cls, port: int = 9090) -> None:
        """Start the metrics HTTP server. O(1)."""
        try:
            start_http_server(port)
            logger.info("MetricsRegistry: server started on port %d", port)
        except Exception as exc:
            logger.error("MetricsRegistry: failed to start server: %s", exc)

    @classmethod
    def record_run(cls, status: str = "success") -> None:
        """Increment pipeline runs. O(1)."""
        cls._PIPELINE_RUNS.labels(status=status).inc()

    @classmethod
    def observe_duration(cls, duration: float) -> None:
        """Observe pipeline latency. O(1)."""
        cls._PIPELINE_DURATION.observe(duration)

    @classmethod
    def record_publish_error(cls, reason: str) -> None:
        """Increment publishing errors. O(1)."""
        cls._PUBLISH_ERRORS.labels(reason=reason).inc()

    @classmethod
    def set_max_trend_score(cls, score: float) -> None:
        """Set highest trend score Gauge. O(1)."""
        cls._TREND_SCORE_MAX.set(score)
