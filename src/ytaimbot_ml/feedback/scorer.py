"""Phase 5 — FeedbackScorer: updates niche weights based on real performance.

Roadmap tasks: T-338 through T-348 (EPIC 5.3 Feedback Scorer)

Algorithm
---------
Exponential Moving Average (EMA) (T-340):
    new_weight = alpha * signal + (1 - alpha) * old_weight
    alpha = 0.3 (learning rate)

Performance Signal (T-341):
    signal = normalize(views * rpm * retention)
    For MVP: signal = views / max_views (simplified)

Safety Bounds (T-342):
    Weight cannot change more than ±20% per update.
    bounded = clip(new, old * 0.8, old * 1.2)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Optional

import numpy as np

if TYPE_CHECKING:
    from ytaimbot_ml.schemas import MetricsSnapshot
    from modules.adapters.base import StorageAdapter

logger = logging.getLogger(__name__)


class FeedbackScorer:
    """Updates and persists niche weights based on video metrics.

    Parameters
    ----------
    storage:
        Persistent storage for weights.
    alpha:
        Learning rate for EMA (default 0.3).
    """

    def __init__(
        self,
        storage: StorageAdapter,
        alpha: float = 0.3,
    ) -> None:
        self._storage = storage
        self.alpha = alpha
        self._weights: Dict[str, float] = {}
        self._load_weights()

    def update(self, niche: str, metrics: MetricsSnapshot) -> float:
        """Update niche weight using EMA and safety bounds.

        Algorithm: EMA O(1) (T-340).

        Parameters
        ----------
        niche:
            Niche name (e.g., "ai_stories").
        metrics:
            Performance snapshot for a video in this niche.

        Returns
        -------
        float
            The new updated weight.
        """
        old_weight = self._weights.get(niche, 1.0)
        
        # 1. Compute performance signal (T-341)
        # For MVP, we use a combination of views and CTR
        # signal range [0.0, 2.0] where 1.0 is "average"
        signal = self._compute_signal(metrics)
        
        # 2. EMA update
        new_weight = self.alpha * signal + (1 - self.alpha) * old_weight
        
        # 3. Safety bounds (±20%) (T-342)
        bounded_weight = np.clip(new_weight, old_weight * 0.8, old_weight * 1.2)
        
        self._weights[niche] = float(bounded_weight)
        
        # 4. Persist (T-344)
        self._save_weights()
        
        logger.info(
            "FeedbackScorer: updated %s weight %.2f -> %.2f (signal=%.2f)",
            niche, old_weight, bounded_weight, signal
        )
        return float(bounded_weight)

    def get_weights(self) -> Dict[str, float]:
        """Return current weights for all niches (T-343)."""
        return dict(self._weights)

    def _compute_signal(self, metrics: MetricsSnapshot) -> float:
        """Translate metrics into a [0, 2] signal score.  O(1)."""
        # Targets: 1000 views = 1.0, 5% CTR = 1.0
        view_score = min(2.0, metrics.views / 1000.0)
        ctr_score = min(2.0, metrics.ctr / 0.05)
        
        return (view_score + ctr_score) / 2.0

    def _load_weights(self) -> None:
        """Load weights from storage if available."""
        # We need a method in storage to load/save arbitrary metadata or specific weights
        if hasattr(self._storage, "load_niche_weights"):
            self._weights = self._storage.load_niche_weights()
        else:
            self._weights = {}

    def _save_weights(self) -> None:
        """Save current weights to storage."""
        if hasattr(self._storage, "save_niche_weights"):
            self._storage.save_niche_weights(self._weights)
