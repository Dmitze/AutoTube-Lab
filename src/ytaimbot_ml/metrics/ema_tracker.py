"""Phase 5 — EMATracker: Exponential Moving Average for YouTube analytics.

Roadmap tasks: T-400 through T-415 (EPIC 5.1 Analytics Feedback)
Depends on:   PipelineResult.analytics

Algorithm
---------
EMA update rule:
  ema_t = α × x_t + (1 - α) × ema_{t-1}
  First update: ema_1 = x_1  (no prior)

  Properties:
  - O(1) time per update, O(1) space
  - Converges after ~3×window observations
  - Exponentially discounts older values

Tracked metrics:
  - ctr        : Click-Through Rate (target ≥ 6%)
  - retention  : 30s retention rate (target ≥ 70%)
  - views      : Raw view count
  - revenue    : Estimated revenue ($)
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class EMATracker:
    """Exponential Moving Average tracker for streaming metric values.

    EMA formula:  ema_t = alpha * x_t + (1 - alpha) * ema_{t-1}
    First update: ema_1 = x_1  (no prior, avoids zero-bias on the first sample)

    Complexity: O(1) per update, O(1) space.

    Parameters
    ----------
    alpha:
        Smoothing factor in the open interval (0, 1).  Higher values make
        the tracker react faster to recent observations.  Default ``0.3``.
    name:
        Human-readable label for this metric (used in logs and serialisation).

    Examples
    --------
    >>> tracker = EMATracker(alpha=0.3, name="ctr")
    >>> tracker.update(0.06)
    >>> tracker.update(0.08)
    >>> 0.05 < tracker.value < 0.10
    True
    """

    def __init__(self, alpha: float = 0.3, name: str = "metric") -> None:
        """Initialise the tracker.

        Parameters
        ----------
        alpha:
            Smoothing factor in (0, 1).  Raises ``ValueError`` if out of range.
        name:
            Label for this metric instance.

        Complexity: O(1).
        """
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}")
        self._alpha: float = alpha
        self._name: str = name
        self._ema: float = 0.0
        self._n: int = 0
        logger.debug("EMATracker '%s' initialised with alpha=%.4f", name, alpha)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update(self, value: float) -> None:
        """Apply one EMA update step.

        On the first call the EMA is set directly to *value* (no prior).
        Subsequent calls apply the standard EMA recurrence.

        Parameters
        ----------
        value:
            New observed metric value.  May be any finite float.

        Complexity: O(1).
        """
        if self._n == 0:
            self._ema = value
        else:
            self._ema = self._alpha * value + (1.0 - self._alpha) * self._ema
        self._n += 1
        logger.debug(
            "EMATracker '%s' updated: value=%.6f → ema=%.6f (n=%d)",
            self._name,
            value,
            self._ema,
            self._n,
        )

    @property
    def value(self) -> float:
        """Current EMA value.

        Returns ``0.0`` before any updates have been applied.

        Complexity: O(1).
        """
        return self._ema

    @property
    def n_samples(self) -> int:
        """Number of ``update()`` calls made so far.

        Complexity: O(1).
        """
        return self._n

    @property
    def alpha(self) -> float:
        """Smoothing factor (read-only after construction).

        Complexity: O(1).
        """
        return self._alpha

    @property
    def name(self) -> str:
        """Human-readable metric label.

        Complexity: O(1).
        """
        return self._name

    def reset(self) -> None:
        """Reset the tracker to its initial (zero-sample) state.

        Does **not** change ``alpha`` or ``name``.

        Complexity: O(1).

        Examples
        --------
        >>> tracker = EMATracker(alpha=0.5, name="views")
        >>> tracker.update(100.0)
        >>> tracker.reset()
        >>> tracker.n_samples
        0
        >>> tracker.value
        0.0
        """
        self._ema = 0.0
        self._n = 0
        logger.debug("EMATracker '%s' reset.", self._name)

    def to_dict(self) -> dict[str, float | str | int]:
        """Serialise tracker state to a flat dictionary.

        Suitable for storing in SQLite or JSON.

        Returns
        -------
        dict
            Keys: ``"name"``, ``"alpha"``, ``"ema"``, ``"n_samples"``.

        Complexity: O(1).

        Examples
        --------
        >>> tracker = EMATracker(alpha=0.3, name="ctr")
        >>> tracker.update(0.07)
        >>> d = tracker.to_dict()
        >>> d["name"]
        'ctr'
        >>> d["n_samples"]
        1
        """
        return {
            "name": self._name,
            "alpha": self._alpha,
            "ema": self._ema,
            "n_samples": self._n,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EMATracker":
        """Deserialise a tracker from a dictionary produced by :meth:`to_dict`.

        Parameters
        ----------
        data:
            Dictionary with keys ``"name"``, ``"alpha"``, ``"ema"``,
            ``"n_samples"``.

        Returns
        -------
        EMATracker
            Restored tracker with the same internal state.

        Complexity: O(1).

        Examples
        --------
        >>> tracker = EMATracker(alpha=0.3, name="retention")
        >>> tracker.update(0.72)
        >>> restored = EMATracker.from_dict(tracker.to_dict())
        >>> abs(restored.value - tracker.value) < 1e-9
        True
        """
        obj = cls(alpha=float(data["alpha"]), name=str(data["name"]))
        obj._ema = float(data["ema"])
        obj._n = int(data["n_samples"])
        return obj

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"EMATracker(name={self._name!r}, alpha={self._alpha}, "
            f"ema={self._ema:.6f}, n={self._n})"
        )


# ---------------------------------------------------------------------------


class MultiMetricTracker:
    """Tracks multiple named EMA metrics simultaneously.

    Used to track CTR, retention_30s, and views per niche.  Each metric
    has its own independent :class:`EMATracker` sharing the same ``alpha``.

    Complexity: O(k) for bulk operations where k = number of metrics.

    Parameters
    ----------
    alpha:
        Shared smoothing factor for all trackers.  Default ``0.3``.
    metrics:
        Optional list of metric names to pre-register.  Additional metrics
        are created on first call to :meth:`update`.

    Examples
    --------
    >>> tracker = MultiMetricTracker(alpha=0.3, metrics=["ctr", "retention"])
    >>> tracker.update("ctr", 0.07)
    >>> tracker.get("ctr") > 0
    True
    """

    def __init__(
        self,
        alpha: float = 0.3,
        metrics: list[str] | None = None,
    ) -> None:
        """Initialise the multi-metric tracker.

        Parameters
        ----------
        alpha:
            Smoothing factor forwarded to every :class:`EMATracker`.
        metrics:
            Names to pre-register.  ``None`` means start empty.

        Complexity: O(k) where k = len(metrics).
        """
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}")
        self._alpha = alpha
        self._trackers: dict[str, EMATracker] = {}
        for m in (metrics or []):
            self._trackers[m] = EMATracker(alpha=alpha, name=m)
        logger.debug(
            "MultiMetricTracker initialised with alpha=%.4f, metrics=%s",
            alpha,
            list(self._trackers),
        )

    # ------------------------------------------------------------------

    def update(self, metric: str, value: float) -> None:
        """Record a new observation for *metric*.

        If *metric* has not been seen before a new :class:`EMATracker` is
        created automatically.

        Parameters
        ----------
        metric:
            Metric name (e.g. ``"ctr"``, ``"retention_30s"``).
        value:
            Observed value.

        Complexity: O(1).
        """
        if metric not in self._trackers:
            self._trackers[metric] = EMATracker(alpha=self._alpha, name=metric)
            logger.debug("MultiMetricTracker: auto-registered metric '%s'.", metric)
        self._trackers[metric].update(value)

    def get(self, metric: str) -> float:
        """Return the current EMA for *metric*.

        Returns ``0.0`` if *metric* is unknown or has received no updates.

        Parameters
        ----------
        metric:
            Metric name.

        Returns
        -------
        float
            Current EMA value or ``0.0``.

        Complexity: O(1).
        """
        tracker = self._trackers.get(metric)
        return tracker.value if tracker is not None else 0.0

    def to_dict(self) -> dict[str, dict]:
        """Serialise all trackers.

        Returns
        -------
        dict
            Mapping of metric name → serialised tracker dict.

        Complexity: O(k).

        Examples
        --------
        >>> t = MultiMetricTracker(alpha=0.3, metrics=["ctr"])
        >>> t.update("ctr", 0.05)
        >>> "ctr" in t.to_dict()
        True
        """
        return {name: tracker.to_dict() for name, tracker in self._trackers.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "MultiMetricTracker":
        """Deserialise from a dictionary produced by :meth:`to_dict`.

        Parameters
        ----------
        data:
            Mapping of metric name → tracker dict (as produced by
            :meth:`EMATracker.to_dict`).

        Returns
        -------
        MultiMetricTracker
            Fully restored instance.

        Complexity: O(k).

        Examples
        --------
        >>> t = MultiMetricTracker(alpha=0.3, metrics=["ctr", "retention"])
        >>> t.update("ctr", 0.08)
        >>> restored = MultiMetricTracker.from_dict(t.to_dict())
        >>> abs(restored.get("ctr") - t.get("ctr")) < 1e-9
        True
        """
        if not data:
            return cls(alpha=0.3, metrics=[])

        # Infer alpha from the first entry so the instance is self-consistent.
        first = next(iter(data.values()))
        alpha = float(first["alpha"])
        obj = cls(alpha=alpha, metrics=[])
        for name, tracker_data in data.items():
            obj._trackers[name] = EMATracker.from_dict(tracker_data)
        return obj

    def __repr__(self) -> str:  # pragma: no cover
        summary = {k: f"{v.value:.4f}" for k, v in self._trackers.items()}
        return f"MultiMetricTracker(alpha={self._alpha}, metrics={summary})"
