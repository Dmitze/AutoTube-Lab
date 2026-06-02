"""Phase 6 — DriftDetector: detects changes in trend distribution using KS-test.

Roadmap tasks: T-396 through T-407 (EPIC 6.2 Drift Detector)
Dependencies:  scipy.stats (ks_2samp)

Algorithm
---------
Kolmogorov-Smirnov Test (T-398):
    Compares two samples (reference vs current).
    If p-value < 0.05, we reject the null hypothesis (distribution changed).

Reservoir Sampling (T-399):
    Maintains a fixed-size sample of a potentially infinite stream.
    O(1) update, O(k) memory.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np
from scipy.stats import ks_2samp

from ytaimbot_ml.schemas import DriftReport

logger = logging.getLogger(__name__)


class KSDriftDetector:
    """Detects data drift in trend scores using the KS-test.

    Parameters
    ----------
    threshold:
        p-value threshold for drift detection (default 0.05).
    """

    def __init__(self, threshold: float = 0.05) -> None:
        self.threshold = threshold

    def check(self, reference: List[float], current: List[float]) -> DriftReport:
        """Perform KS-test between two distributions.  O(n log n).

        Parameters
        ----------
        reference:
            Baseline distribution (e.g., last 30 days).
        current:
            Recent distribution (e.g., last 7 days).

        Returns
        -------
        DriftReport
            Decision and statistics.
        """
        if not reference or not current:
            return DriftReport(statistic=0.0, p_value=1.0, drift_detected=False)

        stat, p_value = ks_2samp(reference, current)
        drift = p_value < self.threshold
        
        logger.info(
            "DriftDetector: KS-stat=%.4f p-value=%.4f drift=%s",
            stat, p_value, drift
        )

        return DriftReport(
            statistic=float(stat),
            p_value=float(p_value),
            drift_detected=drift,
            action="reset_bandit" if drift else "continue"
        )

    def reservoir_sample(
        self, 
        stream: List[float], 
        k: int, 
        rng: Optional[np.random.Generator] = None
    ) -> List[float]:
        """Maintain a representative sample of size k using Vitter's Algorithm R.

        Algorithm: O(n) (T-399).

        Parameters
        ----------
        stream:
            Stream of incoming data points.
        k:
            Reservoir size.
        rng:
            RNG for sampling.

        Returns
        -------
        List[float]
            The sampled reservoir.
        """
        if not rng:
            rng = np.random.default_rng(42)
            
        reservoir = []
        for i, item in enumerate(stream):
            if i < k:
                reservoir.append(item)
            else:
                j = rng.integers(0, i + 1)
                if j < k:
                    reservoir[j] = item
        return reservoir
