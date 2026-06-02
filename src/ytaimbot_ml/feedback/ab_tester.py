"""Phase 5 — ABTester: statistical comparison of content variants (titles/thumbnails).

Roadmap tasks: T-349 through T-359 (EPIC 5.4 A/B Testing Framework)
Dependencies:  scipy.stats (chi2_contingency)

Algorithm
---------
1. Statistical Significance (T-353):
   Chi-Square test for independence between variant and CTR.
   p-value < 0.05 indicates a significant difference.

2. Minimum Sample Size (T-354):
   Requires at least 1000 impressions per variant to avoid premature conclusions.

3. Persistence (T-355):
   Store impression/click counts and results in SQLite.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Literal, Optional, Tuple

import numpy as np
from scipy.stats import chi2_contingency

from ytaimbot_ml.schemas import ABTestResult

if TYPE_CHECKING:
    from modules.adapters.base import StorageAdapter

logger = logging.getLogger(__name__)

_MIN_IMPRESSIONS = 1000


class ABTester:
    """Manages and analyzes A/B tests for video metadata.

    Parameters
    ----------
    storage:
        Persistent storage for test data.
    """

    def __init__(self, storage: StorageAdapter) -> None:
        self._storage = storage
        # Cache for counts: {video_id: {variant_id: {"clicks": int, "impressions": int}}}
        self._counts: Dict[str, Dict[str, Dict[str, int]]] = {}

    def record_impression(self, video_id: str, variant: str) -> None:
        """Record an impression for a specific variant (T-351)."""
        self._ensure_video(video_id)
        self._ensure_variant(video_id, variant)
        self._counts[video_id][variant]["impressions"] += 1

    def record_click(self, video_id: str, variant: str) -> None:
        """Record a click for a specific variant (T-352)."""
        self._ensure_video(video_id)
        self._ensure_variant(video_id, variant)
        self._counts[video_id][variant]["clicks"] += 1

    def analyze(self, video_id: str, variant_type: str = "title") -> ABTestResult:
        """Perform statistical analysis on variants for a video.

        Algorithm: Chi-Square O(1) (T-353).

        Returns
        -------
        ABTestResult
            Decision and significance metrics.
        """
        if video_id not in self._counts or len(self._counts[video_id]) < 2:
            return ABTestResult(video_id=video_id, variant_type=variant_type)

        # We assume 2 variants for simplicity (A vs B)
        variants = list(self._counts[video_id].keys())
        v_a = self._counts[video_id][variants[0]]
        v_b = self._counts[video_id][variants[1]]

        # Check minimum sample size (T-354)
        if v_a["impressions"] < _MIN_IMPRESSIONS or v_b["impressions"] < _MIN_IMPRESSIONS:
            logger.debug("ABTester: sample size too small for %s", video_id)
            return ABTestResult(video_id=video_id, variant_type=variant_type)

        # Contingency table: [[clicks_a, no_clicks_a], [clicks_b, no_clicks_b]]
        table = [
            [v_a["clicks"], v_a["impressions"] - v_a["clicks"]],
            [v_b["clicks"], v_b["impressions"] - v_b["clicks"]],
        ]

        try:
            chi2, p_value, dof, expected = chi2_contingency(table)
            significant = p_value < 0.05
            
            ctr_a = v_a["clicks"] / v_a["impressions"]
            ctr_b = v_b["clicks"] / v_b["impressions"]
            
            winner = "inconclusive"
            if significant:
                winner = variants[0] if ctr_a > ctr_b else variants[1]

            result = ABTestResult(
                video_id=video_id,
                variant_type=variant_type,
                winner=winner,
                p_value=float(p_value),
                significant=significant,
            )
            
            # Persist result (T-355)
            if hasattr(self._storage, "save_ab_test"):
                self._storage.save_ab_test(result)
            
            return result

        except Exception as exc:
            logger.error("ABTester: analysis failed for %s: %s", video_id, exc)
            return ABTestResult(video_id=video_id, variant_type=variant_type)

    def _ensure_video(self, video_id: str) -> None:
        if video_id not in self._counts:
            self._counts[video_id] = {}

    def _ensure_variant(self, video_id: str, variant: str) -> None:
        if variant not in self._counts[video_id]:
            self._counts[video_id][variant] = {"clicks": 0, "impressions": 0}
