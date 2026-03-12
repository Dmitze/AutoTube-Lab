"""Phase 5 — Metrics & Feedback Loop package.

Modules
-------
ema_tracker  : EMA (Exponential Moving Average) for CTR/retention tracking
aggregator   : Prometheus-compatible metrics aggregation + PipelineMetrics snapshot

Algorithm
---------
EMA update: ema_t = alpha x x_t + (1-alpha) x ema_{t-1}  -> O(1) per update
Aggregation: sliding window aggregation                    -> O(window_size)

Status: Implemented -- T-400 / T-416 (Phase 5)
"""
from __future__ import annotations

from ytaimbot_ml.metrics.aggregator import (
    EMATracker,
    MetricsAggregator,
    PipelineMetrics,
)

__all__ = [
    "EMATracker",
    "MetricsAggregator",
    "PipelineMetrics",
]

