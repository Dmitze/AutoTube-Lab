"""Phase 5 — Metrics & Feedback Loop package.

Modules
-------
ema_tracker  : EMA (Exponential Moving Average) for CTR/retention tracking
aggregator   : Prometheus-compatible metrics aggregation

Algorithm
---------
EMA update: ema_t = α × x_t + (1-α) × ema_{t-1}  → O(1) per update
Aggregation: sliding window aggregation              → O(window_size)

Status: 🔲 Pending — T-400 (Phase 5)
"""
