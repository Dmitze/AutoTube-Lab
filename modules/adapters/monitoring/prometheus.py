"""Phase 7 — PrometheusExporter: exports pipeline metrics for Prometheus scraping.

Roadmap tasks: T-550 through T-565 (EPIC 7.2 Monitoring)
Depends on:   prometheus_client library (optional — degrades gracefully)

Endpoint: http://bot:8000/metrics (scraped every 15s by Prometheus)

Algorithm
---------
Metric types:
  Counter    : monotonically increasing (videos published, errors)
  Gauge      : current value (EMA CTR, retention, quota used)
  Histogram  : distribution (pipeline duration, render time)

  All operations: O(1) update, O(m) scrape where m = metric count
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    log.warning(
        "prometheus_client not installed — metrics export disabled. "
        "Install with: pip install prometheus-client>=0.19"
    )

# ---------------------------------------------------------------------------
# Module-level metric singletons (registered once to avoid duplicate errors)
# ---------------------------------------------------------------------------
if _PROMETHEUS_AVAILABLE:
    from prometheus_client import REGISTRY
    # Prevent duplicate registration during pytest re-imports
    for _name in list(REGISTRY._names_to_collectors.keys()):
        if _name.startswith("ytaimbot_"):
            try:
                REGISTRY.unregister(REGISTRY._names_to_collectors[_name])
            except KeyError:
                pass

    _PIPELINE_RUNS = Counter(
        "ytaimbot_pipeline_runs_total",
        "Total pipeline runs by status",
        ["status"],
    )
    _PIPELINE_DURATION = Histogram(
        "ytaimbot_pipeline_duration_seconds",
        "Pipeline execution time in seconds",
        buckets=[30, 60, 120, 300, 600],
    )
    _PUBLISH_ERRORS = Counter(
        "ytaimbot_publish_errors_total",
        "Publish failures by reason",
        ["reason"],
    )
    _TREND_SCORE_MAX = Gauge(
        "ytaimbot_trend_score_max",
        "Highest trend score in last run",
    )
    _CTR_EMA = Gauge(
        "ytaimbot_ctr_ema",
        "EMA click-through rate (rolling average)",
    )
    _RETENTION_EMA = Gauge(
        "ytaimbot_retention_ema",
        "EMA 30-second retention (rolling average)",
    )
    _YT_QUOTA_USED = Gauge(
        "ytaimbot_yt_quota_used",
        "YouTube API quota used today",
    )
    _GATE_PASS_RATIO = Gauge(
        "ytaimbot_gate_pass_ratio",
        "Bayesian gate pass ratio (approved/total)",
    )
    _VIDEOS_PUBLISHED = Counter(
        "ytaimbot_videos_published_total",
        "Total videos published",
    )
else:
    _PIPELINE_RUNS = None
    _PIPELINE_DURATION = None
    _PUBLISH_ERRORS = None
    _TREND_SCORE_MAX = None
    _CTR_EMA = None
    _RETENTION_EMA = None
    _YT_QUOTA_USED = None
    _GATE_PASS_RATIO = None
    _VIDEOS_PUBLISHED = None


class PrometheusExporter:
    """Prometheus metrics exporter for the YTAIMBot pipeline.

    Exposes custom metrics on an HTTP endpoint scraped by Prometheus.
    Gracefully degrades (no-op) if prometheus_client is not installed.

    Algorithm: O(1) per metric update; O(m) per scrape (m = metric count)

    Parameters
    ----------
    port:
        HTTP port to expose the /metrics endpoint on. Default 8000.
    enabled:
        If False, all calls are no-ops regardless of prometheus_client
        availability. Useful for testing without side effects.

    Examples
    --------
    >>> exp = PrometheusExporter()
    >>> exp.record_pipeline_run(status="success", duration_seconds=45.2)
    >>> exp.record_trend_score(0.87)
    >>> exp.record_ctr_ema(0.09)
    >>> exp.record_retention_ema(0.71)
    >>> exp.record_quota_used(1200)
    >>> exp.record_gate_ratio(pass_count=4, total=5)
    >>> exp.record_publish_error(reason="compliance")
    >>> exp.record_video_published()
    """

    def __init__(self, port: int = 8000, enabled: bool = True) -> None:
        self.port = port
        self.enabled = enabled and _PROMETHEUS_AVAILABLE
        if enabled and not _PROMETHEUS_AVAILABLE:
            log.debug("PrometheusExporter created but prometheus_client unavailable — no-op mode.")

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------

    def start_server(self) -> None:
        """Start the Prometheus HTTP metrics server on self.port.

        Algorithm: O(1) — single socket bind.

        Examples
        --------
        >>> exp = PrometheusExporter(port=8000)
        >>> exp.start_server()  # starts /metrics endpoint
        """
        if not self.enabled:
            log.debug("PrometheusExporter.start_server() called but exporter is disabled.")
            return
        try:
            start_http_server(self.port)
            log.info("Prometheus metrics server started on port %d", self.port)
        except Exception:
            log.exception("Failed to start Prometheus metrics server on port %d", self.port)

    # ------------------------------------------------------------------
    # Metric recorders
    # ------------------------------------------------------------------

    def record_pipeline_run(self, status: str, duration_seconds: float) -> None:
        """Record a completed pipeline run.

        Algorithm: O(1) — counter increment + histogram observe.

        Parameters
        ----------
        status:
            One of "success", "error", or "dry_run".
        duration_seconds:
            Wall-clock time the run took.

        Examples
        --------
        >>> exp = PrometheusExporter()
        >>> exp.record_pipeline_run(status="success", duration_seconds=45.2)
        """
        if not self.enabled:
            return
        try:
            _PIPELINE_RUNS.labels(status=status).inc()
            _PIPELINE_DURATION.observe(duration_seconds)
            log.debug("Recorded pipeline run: status=%s duration=%.2fs", status, duration_seconds)
        except Exception:
            log.exception("Error recording pipeline run metric")

    def record_trend_score(self, score: float) -> None:
        """Update the maximum trend score gauge.

        Algorithm: O(1).

        Parameters
        ----------
        score:
            Highest L2 trend score from the current run (0.0–1.0+).

        Examples
        --------
        >>> exp = PrometheusExporter()
        >>> exp.record_trend_score(0.87)
        """
        if not self.enabled:
            return
        try:
            _TREND_SCORE_MAX.set(score)
        except Exception:
            log.exception("Error recording trend score metric")

    def record_ctr_ema(self, ctr: float) -> None:
        """Update the EMA click-through rate gauge.

        Algorithm: O(1).

        Parameters
        ----------
        ctr:
            Rolling EMA of CTR (e.g. 0.06 for 6%).

        Examples
        --------
        >>> exp = PrometheusExporter()
        >>> exp.record_ctr_ema(0.09)
        """
        if not self.enabled:
            return
        try:
            _CTR_EMA.set(ctr)
        except Exception:
            log.exception("Error recording CTR EMA metric")

    def record_retention_ema(self, retention: float) -> None:
        """Update the EMA 30-second retention gauge.

        Algorithm: O(1).

        Parameters
        ----------
        retention:
            Rolling EMA of 30s retention rate (e.g. 0.71 for 71%).

        Examples
        --------
        >>> exp = PrometheusExporter()
        >>> exp.record_retention_ema(0.71)
        """
        if not self.enabled:
            return
        try:
            _RETENTION_EMA.set(retention)
        except Exception:
            log.exception("Error recording retention EMA metric")

    def record_quota_used(self, quota: int) -> None:
        """Update the YouTube API quota used gauge.

        Algorithm: O(1).

        Parameters
        ----------
        quota:
            Number of quota units consumed today (max 10 000/day).

        Examples
        --------
        >>> exp = PrometheusExporter()
        >>> exp.record_quota_used(1200)
        """
        if not self.enabled:
            return
        try:
            _YT_QUOTA_USED.set(quota)
        except Exception:
            log.exception("Error recording quota used metric")

    def record_gate_ratio(self, pass_count: int, total: int) -> None:
        """Update the Bayesian gate pass ratio gauge.

        Algorithm: O(1).

        Parameters
        ----------
        pass_count:
            Number of content plans that passed the quality gate.
        total:
            Total number of content plans evaluated.

        Examples
        --------
        >>> exp = PrometheusExporter()
        >>> exp.record_gate_ratio(pass_count=4, total=5)
        """
        if not self.enabled:
            return
        try:
            ratio = pass_count / total if total > 0 else 0.0
            _GATE_PASS_RATIO.set(ratio)
        except Exception:
            log.exception("Error recording gate pass ratio metric")

    def record_publish_error(self, reason: str = "unknown") -> None:
        """Increment the publish error counter for a given reason.

        Algorithm: O(1).

        Parameters
        ----------
        reason:
            One of "quota", "auth", "compliance", or "unknown".

        Examples
        --------
        >>> exp = PrometheusExporter()
        >>> exp.record_publish_error(reason="compliance")
        """
        if not self.enabled:
            return
        try:
            _PUBLISH_ERRORS.labels(reason=reason).inc()
            log.debug("Recorded publish error: reason=%s", reason)
        except Exception:
            log.exception("Error recording publish error metric")

    def record_video_published(self) -> None:
        """Increment the total videos published counter.

        Algorithm: O(1).

        Examples
        --------
        >>> exp = PrometheusExporter()
        >>> exp.record_video_published()
        """
        if not self.enabled:
            return
        try:
            _VIDEOS_PUBLISHED.inc()
            log.debug("Recorded video published")
        except Exception:
            log.exception("Error recording video published metric")

    # ------------------------------------------------------------------
    # Backward-compatibility shim
    # ------------------------------------------------------------------

    def record(self, metric_name: str, value: float) -> None:
        """Legacy metric recorder — dispatches to the typed methods above.

        Supported metric_name values: "ctr_ema", "retention_ema",
        "trend_score_max", "yt_quota_used".  Unknown names are logged and
        ignored.

        Algorithm: O(1) dispatch.

        Parameters
        ----------
        metric_name:
            Logical metric name (snake_case, without the ytaimbot_ prefix).
        value:
            Numeric value to record.

        Examples
        --------
        >>> exp = PrometheusExporter()
        >>> exp.record("ctr_ema", 0.08)
        """
        _dispatch: dict[str, object] = {
            "ctr_ema": lambda v: self.record_ctr_ema(v),
            "retention_ema": lambda v: self.record_retention_ema(v),
            "trend_score_max": lambda v: self.record_trend_score(v),
            "yt_quota_used": lambda v: self.record_quota_used(int(v)),
        }
        handler = _dispatch.get(metric_name)
        if handler is None:
            log.warning("PrometheusExporter.record(): unknown metric '%s' — ignoring", metric_name)
            return
        handler(value)  # type: ignore[operator]
