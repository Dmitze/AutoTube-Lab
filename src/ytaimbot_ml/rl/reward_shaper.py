"""Phase 6 — RewardShaper: normalises raw YouTube metrics into bandit rewards.

Roadmap tasks: T-521 through T-530 (EPIC 6.2 Reward Shaping)
Depends on:   EMATracker, UCB1Bandit

Algorithm
---------
Weighted-target normalisation:
    raw = (ctr / CTR_TARGET)         * CTR_WEIGHT
        + (retention / RET_TARGET)   * RETENTION_WEIGHT
        + log1p(views) / log1p(VIEWS_TARGET) * VIEWS_WEIGHT
    reward = clip(raw, 0.0, 1.0)

Welford's online variance (O(1) per sample, numerically stable):
    M_k = M_{k-1} + (x_k - M_{k-1}) / k
    S_k = S_{k-1} + (x_k - M_{k-1}) × (x_k - M_k)
    σ²  = S_k / (k - 1)   for k ≥ 2, else 0.0
"""
from __future__ import annotations

import logging
import math

import numpy as np

logger = logging.getLogger(__name__)


class RewardShaper:
    """Shapes raw YouTube metrics into a scalar reward in [0, 1].

    Reward formula:
        raw = (ctr / CTR_TARGET)               * CTR_WEIGHT
            + (retention / RETENTION_TARGET)   * RETENTION_WEIGHT
            + log1p(views) / log1p(VIEWS_TARGET) * VIEWS_WEIGHT
        reward = clip(raw, 0.0, 1.0)

    Uses Welford's online algorithm for running mean/variance (O(1)).

    Complexity: O(1) per :meth:`shape` call.

    Parameters
    ----------
    (none — all targets/weights are class-level constants)

    Examples
    --------
    >>> shaper = RewardShaper()
    >>> r = shaper.shape(ctr=0.07, retention_30s=0.72, views=5000)
    >>> 0.0 <= r <= 1.0
    True
    """

    # ------------------------------------------------------------------
    # Target metrics (project-level KPIs)
    # ------------------------------------------------------------------

    CTR_TARGET: float = 0.06        # 6 % CTR target
    RETENTION_TARGET: float = 0.70  # 70 % 30 s retention target
    VIEWS_TARGET: int = 10_000      # 10 k views per-video target

    # ------------------------------------------------------------------
    # Reward weights (must sum to 1.0)
    # ------------------------------------------------------------------

    CTR_WEIGHT: float = 0.4
    RETENTION_WEIGHT: float = 0.4
    VIEWS_WEIGHT: float = 0.2

    def __init__(self) -> None:
        """Initialise Welford online-statistics accumulators.

        Complexity: O(1).
        """
        self._n: int = 0
        self._m: float = 0.0   # running mean
        self._s: float = 0.0   # running sum of squared deviations
        logger.debug("RewardShaper initialised.")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def shape(self, ctr: float, retention_30s: float, views: int) -> float:
        """Compute a scalar reward in ``[0.0, 1.0]`` from raw video metrics.

        Each metric component is normalised by its project target and then
        combined with the corresponding weight.  The result is clipped to
        ensure valid bandit rewards.  The shaped value is also fed into the
        Welford accumulator so callers can inspect running statistics.

        Parameters
        ----------
        ctr:
            Click-through rate, e.g. ``0.07`` for 7 %.
        retention_30s:
            Fraction of viewers who watched ≥ 30 s, e.g. ``0.72``.
        views:
            Raw view count (non-negative integer).

        Returns
        -------
        float
            Scalar reward in ``[0.0, 1.0]``.

        Complexity: O(1).

        Examples
        --------
        >>> s = RewardShaper()
        >>> r = s.shape(ctr=0.06, retention_30s=0.70, views=10_000)
        >>> abs(r - 1.0) < 1e-6
        True
        >>> s.n_samples
        1
        """
        ctr_term = (ctr / self.CTR_TARGET) * self.CTR_WEIGHT
        ret_term = (retention_30s / self.RETENTION_TARGET) * self.RETENTION_WEIGHT
        # log1p normalisation keeps views-term in a comparable range.
        views_term = (
            math.log1p(max(views, 0))
            / math.log1p(self.VIEWS_TARGET)
        ) * self.VIEWS_WEIGHT

        raw = ctr_term + ret_term + views_term
        reward = float(np.clip(raw, 0.0, 1.0))
        self._welford_update(reward)
        logger.debug(
            "RewardShaper.shape: ctr=%.4f ret=%.4f views=%d → reward=%.4f",
            ctr,
            retention_30s,
            views,
            reward,
        )
        return reward

    def _welford_update(self, x: float) -> None:
        """Update running mean and variance using Welford's algorithm.

        Numerically stable single-pass algorithm:
            M_k = M_{k-1} + (x_k - M_{k-1}) / k
            S_k = S_{k-1} + (x_k - M_{k-1}) × (x_k - M_k)

        Parameters
        ----------
        x:
            New observation to incorporate.

        Complexity: O(1).
        """
        self._n += 1
        delta = x - self._m
        self._m += delta / self._n
        delta2 = x - self._m
        self._s += delta * delta2

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def mean(self) -> float:
        """Running mean of all shaped reward values.

        Returns ``0.0`` before any calls to :meth:`shape`.

        Complexity: O(1).
        """
        return self._m

    @property
    def variance(self) -> float:
        """Running sample variance of all shaped reward values.

        Returns ``0.0`` for fewer than two samples.

        Complexity: O(1).
        """
        return self._s / (self._n - 1) if self._n >= 2 else 0.0

    @property
    def n_samples(self) -> int:
        """Number of :meth:`shape` calls recorded.

        Complexity: O(1).
        """
        return self._n

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RewardShaper(n={self._n}, mean={self._m:.4f}, "
            f"variance={self.variance:.6f})"
        )
