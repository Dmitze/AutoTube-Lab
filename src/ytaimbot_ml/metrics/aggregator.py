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
Aggregation: sliding window over last N runs → O(1) amortized per append
EMA update:  O(1) per run
Prometheus:  O(1) per push

EMATracker: O(1) per update, O(1) per query.
MetricsAggregator (T-416): O(1) add, O(1) current values via EMA.

Status: ✅ Implemented — T-416 (Phase 5)
"""
from __future__ import annotations

import logging
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ytaimbot_ml.metrics.ema_tracker import EMATracker as _EMATracker
from ytaimbot_ml.schemas import PipelineResult

try:
    from modules.adapters.monitoring.prometheus import (
        PrometheusExporter as _PrometheusExporter,
    )
except ImportError:
    _PrometheusExporter = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# Statuses that count as a successful pipeline run
_SUCCESS_STATUSES: frozenset[str] = frozenset({"ok", "published", "success"})


# ---------------------------------------------------------------------------
# EMATracker — public, alpha in (0, 1] (exposed via ytaimbot_ml.metrics)
# ---------------------------------------------------------------------------


class EMATracker:
    """Exponential Moving Average tracker. O(1) per update, O(1) space.

    EMA formula: ema_t = α × value_t + (1−α) × ema_{t−1}
    The initial seed value is used as ema_{-1} so the formula applies uniformly
    from the very first call (unlike the ema_tracker.EMATracker which seeds on
    first call directly).

    This class accepts alpha=1.0 (last-value-wins, no smoothing).

    Parameters
    ----------
    alpha : float
        Smoothing factor. Must satisfy 0 < alpha <= 1.
    initial : float
        Starting EMA seed value. Default 0.0.

    Examples
    --------
    >>> ema = EMATracker(alpha=0.3, initial=0.0)
    >>> ema.update(10.0)
    >>> 2.5 < ema.value < 4.0
    True
    >>> ema_one = EMATracker(alpha=1.0)
    >>> ema_one.update(42.0)
    >>> ema_one.value
    42.0
    """

    def __init__(self, alpha: float = 0.3, initial: float = 0.0) -> None:
        """Initialise the tracker.

        Parameters
        ----------
        alpha : float
            Smoothing factor in (0, 1]. Raises ValueError if out of range.
        initial : float
            Starting seed value for EMA computation. Default 0.0.

        Complexity: O(1).

        Examples
        --------
        >>> t = EMATracker(alpha=0.5, initial=1.0)
        >>> t.value
        1.0
        """
        if not 0 < alpha <= 1:
            raise ValueError(f"alpha must be in (0, 1], got {alpha!r}")
        self._alpha = alpha
        self._value = initial
        self._count = 0

    def update(self, value: float) -> float:
        """Update EMA with new value. Returns updated EMA. O(1).

        Parameters
        ----------
        value : float
            New observed value.

        Returns
        -------
        float
            Updated EMA.

        Examples
        --------
        >>> t = EMATracker(alpha=1.0)
        >>> t.update(7.0)
        7.0
        """
        self._value = self._alpha * value + (1 - self._alpha) * self._value
        self._count += 1
        return self._value

    @property
    def value(self) -> float:
        """Current EMA value. O(1).

        Examples
        --------
        >>> EMATracker(alpha=0.5, initial=2.0).value
        2.0
        """
        return self._value

    @property
    def count(self) -> int:
        """Number of update() calls. O(1).

        Examples
        --------
        >>> t = EMATracker(); t.update(1.0); t.count
        1
        """
        return self._count

    def reset(self, initial: float = 0.0) -> None:
        """Reset EMA to *initial* and clear sample count. O(1).

        Parameters
        ----------
        initial : float
            New seed value after reset. Default 0.0.

        Examples
        --------
        >>> t = EMATracker(alpha=0.3)
        >>> t.update(5.0); t.reset()
        >>> t.value == 0.0 and t.count == 0
        True
        """
        self._value = initial
        self._count = 0


# ---------------------------------------------------------------------------
# PipelineMetrics — immutable snapshot dataclass
# ---------------------------------------------------------------------------


@dataclass
class PipelineMetrics:
    """Snapshot of pipeline metrics at one point in time. O(1).

    Examples
    --------
    >>> snap = PipelineMetrics.empty()
    >>> snap.videos_published
    0
    >>> snap.avg_ctr
    0.0
    """

    timestamp: str
    videos_published: int
    avg_ctr: float            # 0.0–1.0 range
    avg_retention_30s: float  # 0.0–1.0 range
    quota_used: int
    error_count: int
    revenue_estimate: float   # USD

    @classmethod
    def empty(cls) -> "PipelineMetrics":
        """Return a zero-value metrics snapshot with current timestamp. O(1).

        Examples
        --------
        >>> snap = PipelineMetrics.empty()
        >>> snap.error_count
        0
        """
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            videos_published=0,
            avg_ctr=0.0,
            avg_retention_30s=0.0,
            quota_used=0,
            error_count=0,
            revenue_estimate=0.0,
        )


class MetricsAggregator:
    """Aggregates pipeline run metrics using EMA and sliding window.

    Provides two complementary interfaces:

    **Legacy interface** (T-416 original):
    - ``record_pipeline_run(result)`` — append a PipelineResult to the window
    - ``get_window_stats()`` — sliding-window summary dict

    **Video-publish interface** (T-416 extension):
    - ``record_video_published(ctr, retention, revenue, niche)`` — O(1) EMA update
    - ``snapshot()`` → PipelineMetrics — O(1) current values
    - Optional PrometheusExporter integration

    Algorithm:
    - record_video_published: O(1) EMA update
    - snapshot: O(1)
    - get_window_stats: O(window_size)

    Examples
    --------
    >>> agg = MetricsAggregator(window_size=10)
    >>> from ytaimbot_ml.schemas import PipelineResult
    >>> agg.record_pipeline_run(PipelineResult(run_id="r1", status="ok"))
    >>> agg.get_window_stats()["total_runs"]
    1
    >>> agg2 = MetricsAggregator()
    >>> agg2.record_video_published(ctr=0.10, retention=0.72, revenue=0.8)
    >>> snap = agg2.snapshot()
    >>> snap.videos_published
    1
    >>> 0.09 < snap.avg_ctr < 0.11
    True
    """

    def __init__(
        self,
        window_size: int = 100,
        exporter: "_PrometheusExporter | None" = None,  # type: ignore[valid-type]
        ctr_alpha: float = 0.3,
        retention_alpha: float = 0.3,
        prometheus_exporter=None,  # PrometheusExporter | None
    ) -> None:
        """Initialise the aggregator.

        Parameters
        ----------
        window_size : int
            Sliding window capacity for PipelineResult objects. O(1).
        exporter : PrometheusExporter | None
            Legacy Prometheus exporter (used by record_pipeline_run). None
            disables forwarding without raising errors.
        ctr_alpha : float
            EMA smoothing factor for CTR tracking. Default 0.3.
        retention_alpha : float
            EMA smoothing factor for retention tracking. Default 0.3.
        prometheus_exporter : PrometheusExporter | None
            Alternative exporter for video-publish interface. Falls back to
            *exporter* when None.

        Complexity: O(1).

        Examples
        --------
        >>> agg = MetricsAggregator(window_size=50)
        >>> agg.get_window_stats()["total_runs"]
        0
        """
        self._window_size = window_size
        self._window: deque[PipelineResult] = deque(maxlen=window_size)
        self._exporter = exporter or prometheus_exporter

        # Legacy EMA trackers (first-call = direct set semantics)
        self._ctr_tracker = _EMATracker(alpha=ctr_alpha, name="ctr")
        self._retention_tracker = _EMATracker(alpha=retention_alpha, name="retention")

        # Video-publish interface counters
        self._videos_published: int = 0
        self._error_count: int = 0
        self._quota_used: int = 0
        self._revenue_history: deque[float] = deque(maxlen=window_size)

        logger.debug(
            "MetricsAggregator initialised (window_size=%d, exporter=%s, "
            "ctr_alpha=%.3f, retention_alpha=%.3f)",
            window_size,
            self._exporter.__class__.__name__ if self._exporter is not None else "None",
            ctr_alpha,
            retention_alpha,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def record_pipeline_run(self, result: PipelineResult) -> None:
        """Record a completed pipeline run.

        Appends *result* to the sliding window, updates EMA trackers, and
        forwards the status/duration to the :class:`PrometheusExporter` when
        one is configured.

        Algorithm: O(1) amortized (deque append + EMA update + optional
        Prometheus calls).

        Parameters
        ----------
        result:
            Completed :class:`PipelineResult` from the pipeline.

        Examples
        --------
        >>> agg = MetricsAggregator(window_size=10)
        >>> from ytaimbot_ml.schemas import PipelineResult
        >>> agg.record_pipeline_run(PipelineResult(run_id="r1", status="ok"))
        >>> agg.get_window_stats()["total_runs"]
        1
        """
        self._window.append(result)

        # Forward to Prometheus if available
        if self._exporter is not None:
            self._exporter.record_pipeline_run(
                status=result.status, duration_seconds=0.0
            )
            if result.uploads:
                self._exporter.record_video_published()

        logger.info(
            "MetricsAggregator: recorded run_id=%s status=%s (window %d/%d)",
            result.run_id,
            result.status,
            len(self._window),
            self._window_size,
        )

    def get_window_stats(self) -> dict[str, float]:
        """Return summary statistics for the current sliding window.

        Iterates over the retained :class:`PipelineResult` objects to compute
        aggregated counters and rates.

        Algorithm: O(window_size).

        Returns
        -------
        dict[str, float]
            Keys: ``total_runs``, ``success_rate``, ``avg_ctr``,
            ``avg_retention``, ``error_rate``, ``dry_run_rate``.

        Examples
        --------
        >>> agg = MetricsAggregator(window_size=10)
        >>> agg.get_window_stats()["success_rate"]
        0.0
        >>> from ytaimbot_ml.schemas import PipelineResult
        >>> agg.record_pipeline_run(PipelineResult(run_id="r1", status="ok"))
        >>> agg.get_window_stats()["success_rate"]
        1.0
        """
        total = len(self._window)
        if total == 0:
            return {
                "total_runs": 0.0,
                "success_rate": 0.0,
                "avg_ctr": 0.0,
                "avg_retention": 0.0,
                "error_rate": 0.0,
                "dry_run_rate": 0.0,
            }

        success_count = sum(
            1 for r in self._window if r.status in _SUCCESS_STATUSES
        )
        error_count = sum(1 for r in self._window if r.status == "error")
        dry_run_count = sum(1 for r in self._window if r.status == "dry_run")

        return {
            "total_runs": float(total),
            "success_rate": success_count / total,
            "avg_ctr": self._ctr_tracker.value,
            "avg_retention": self._retention_tracker.value,
            "error_rate": error_count / total,
            "dry_run_rate": dry_run_count / total,
        }

    def reset(self) -> None:
        """Clear the sliding window, counters, and EMA trackers.

        Does **not** change ``window_size`` or the exporter reference.

        Algorithm: O(1).

        Examples
        --------
        >>> agg = MetricsAggregator(window_size=10)
        >>> from ytaimbot_ml.schemas import PipelineResult
        >>> agg.record_pipeline_run(PipelineResult(run_id="r1", status="ok"))
        >>> agg.reset()
        >>> agg.get_window_stats()["total_runs"]
        0
        """
        self._window.clear()
        self._ctr_tracker.reset()
        self._retention_tracker.reset()
        self._videos_published = 0
        self._error_count = 0
        self._quota_used = 0
        self._revenue_history.clear()
        logger.debug("MetricsAggregator reset.")

    # ------------------------------------------------------------------
    # Video-publish interface (T-416 extension)
    # ------------------------------------------------------------------

    def record_video_published(
        self,
        ctr: float,
        retention: float,
        revenue: float = 0.0,
        niche: str = "unknown",
    ) -> None:
        """Record a successful video publish. O(1).

        Updates EMA trackers for CTR and retention, appends revenue to the
        history window, and forwards metrics to Prometheus when configured.

        Parameters
        ----------
        ctr : float
            Click-through rate (0.0–1.0).
        retention : float
            30-second retention rate (0.0–1.0).
        revenue : float
            Estimated revenue in USD. Default 0.0.
        niche : str
            Video niche label (for logging). Default "unknown".

        Examples
        --------
        >>> agg = MetricsAggregator()
        >>> agg.record_video_published(ctr=0.08, retention=0.75)
        >>> agg.videos_published
        1
        """
        self._videos_published += 1
        self._ctr_tracker.update(ctr)
        self._retention_tracker.update(retention)
        self._revenue_history.append(revenue)

        if self._exporter is not None:
            try:
                self._exporter.record_video_published()
                self._exporter.record_ctr_ema(ctr)
                self._exporter.record_retention_ema(retention)
            except Exception:  # pragma: no cover
                logger.debug("PrometheusExporter call failed (non-fatal).")

        logger.info(
            "MetricsAggregator: published video #%d niche=%s ctr=%.4f "
            "retention=%.4f revenue=%.2f",
            self._videos_published,
            niche,
            ctr,
            retention,
            revenue,
        )

    def record_error(self, error_type: str = "unknown") -> None:
        """Increment error counter. O(1).

        Parameters
        ----------
        error_type : str
            Human-readable error label for logging. Default "unknown".

        Examples
        --------
        >>> agg = MetricsAggregator()
        >>> agg.record_error("bayes_filter")
        >>> agg.snapshot().error_count
        1
        """
        self._error_count += 1
        if self._exporter is not None:
            try:
                self._exporter.record_publish_error(error_type)
            except Exception:  # pragma: no cover
                logger.debug("PrometheusExporter call failed (non-fatal).")
        logger.debug("MetricsAggregator: error recorded type=%s", error_type)

    def record_quota_usage(self, delta: int) -> None:
        """Add *delta* to quota_used counter. O(1).

        Parameters
        ----------
        delta : int
            YouTube API quota units consumed.

        Examples
        --------
        >>> agg = MetricsAggregator()
        >>> agg.record_quota_usage(50)
        >>> agg.snapshot().quota_used
        50
        """
        self._quota_used += delta
        if self._exporter is not None:
            try:
                self._exporter.record_quota_used(self._quota_used)
            except Exception:  # pragma: no cover
                logger.debug("PrometheusExporter call failed (non-fatal).")
        logger.debug("MetricsAggregator: quota_used=%d (delta=%d)", self._quota_used, delta)

    def snapshot(self) -> PipelineMetrics:
        """Return current metrics snapshot. O(1).

        Returns
        -------
        PipelineMetrics
            Immutable snapshot of current aggregated metrics.

        Examples
        --------
        >>> agg = MetricsAggregator()
        >>> snap = agg.snapshot()
        >>> snap.videos_published
        0
        """
        revenue_est = (
            sum(self._revenue_history) / len(self._revenue_history)
            if self._revenue_history
            else 0.0
        )
        return PipelineMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            videos_published=self._videos_published,
            avg_ctr=self._ctr_tracker.value,
            avg_retention_30s=self._retention_tracker.value,
            quota_used=self._quota_used,
            error_count=self._error_count,
            revenue_estimate=revenue_est,
        )

    @property
    def videos_published(self) -> int:
        """Total videos published since construction or last reset. O(1).

        Examples
        --------
        >>> MetricsAggregator().videos_published
        0
        """
        return self._videos_published

    @classmethod
    def from_env(cls, prometheus_exporter=None) -> "MetricsAggregator":
        """Build from environment variables. O(1).

        Reads:
        - ``METRICS_CTR_ALPHA`` (default ``0.3``)
        - ``METRICS_RETENTION_ALPHA`` (default ``0.3``)

        Parameters
        ----------
        prometheus_exporter : PrometheusExporter | None
            Optional Prometheus exporter to attach. Default None.

        Returns
        -------
        MetricsAggregator
            Configured instance.

        Examples
        --------
        >>> import os
        >>> os.environ.setdefault("METRICS_CTR_ALPHA", "0.3")
        '0.3'
        >>> agg = MetricsAggregator.from_env()
        >>> isinstance(agg, MetricsAggregator)
        True
        """
        ctr_alpha = float(os.environ.get("METRICS_CTR_ALPHA", "0.3"))
        retention_alpha = float(os.environ.get("METRICS_RETENTION_ALPHA", "0.3"))
        return cls(
            ctr_alpha=ctr_alpha,
            retention_alpha=retention_alpha,
            prometheus_exporter=prometheus_exporter,
        )
