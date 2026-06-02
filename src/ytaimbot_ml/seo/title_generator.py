"""Phase 3 — TitleGenerator: CTR-optimized YouTube title generation.

Roadmap tasks: T-213 through T-225 (EPIC 3.5)

Algorithm
---------
CTR Scoring (T-216, T-217):
    Weighted sum of features for predicted CTR:
    - has_number:      0.20
    - has_question:    0.15
    - has_power_word:  0.25
    - length_optimal:  0.20 (40-60 chars)
    - has_keyword:     0.20

    Complexity: O(n_features) = O(1)

Selection:
    Select max score variant from 3 candidates.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ytaimbot_ml.schemas import ContentPlan

logger = logging.getLogger(__name__)

# Standard power words to drive CTR (T-214)
POWER_WORDS = [
    "secret", "hidden", "mistake", "error", "free", "easy", "simple",
    "shocking", "amazing", "insane", "how-to", "tips", "tricks",
    "beginner", "master", "guide", "roadmap", "hacks", "exposed",
    "don't", "must", "know", "before", "buy", "try", "scam", "real",
]


class TitleGenerator:
    """Generates and ranks CTR-optimized YouTube titles.

    Parameters
    ----------
    language:
        ISO 639-1 language code (default "en").
    """

    def __init__(self, language: str = "en") -> None:
        self.language = language

    def generate_variants(self, plan: ContentPlan, n: int = 3) -> List[str]:
        """Generate N title variants based on ContentPlan.

        Algorithm: O(n_variants).  Simple rule-based for MVP.

        Parameters
        ----------
        plan:
            ContentPlan with title and keywords.
        n:
            Number of variants to generate.

        Returns
        -------
        List[str]
            Title strings.
        """
        variants = []
        base_title = plan.title or "New Video"
        keywords = plan.keywords or ["tutorial"]
        kw = keywords[0].title()

        # 1. Direct topic title with context
        variants.append(f"{base_title} | Ultimate {kw} Tutorial for Beginners (2026)")

        # 2. Power word title
        power = POWER_WORDS[0].title() if POWER_WORDS else "Amazing"
        variants.append(f"{power}: {base_title} - Everything You Need to Know!")

        # 3. List/Number title
        variants.append(f"Top 5 {kw} Tips You Must Know Before Starting in 2026")

        # Ensure unique and length-bounded
        seen = set()
        final = []
        for v in variants:
            v = self._validate_length(v)
            if v not in seen:
                seen.add(v)
                final.append(v)
        
        return final[:n]

    def ctr_score(self, title: str, plan: Optional[ContentPlan] = None) -> float:
        """Predict CTR score for a given title [0.0, 1.0].

        Algorithm: Weighted sum (T-216) — O(1).

        Parameters
        ----------
        title:
            Candidate title string.
        plan:
            Optional ContentPlan context for keyword matching.

        Returns
        -------
        float
            Predicted CTR score.
        """
        score = 0.0
        title_lower = title.lower()

        # Feature 1: Has number (0.20)
        if any(c.isdigit() for c in title):
            score += 0.20

        # Feature 2: Has question (0.15)
        if "?" in title:
            score += 0.15

        # Feature 3: Has power word (0.25)
        if any(p in title_lower for p in POWER_WORDS):
            score += 0.25

        # Feature 4: Length optimal (40-60 chars) (0.20)
        if 40 <= len(title) <= 60:
            score += 0.20

        # Feature 5: Has keyword (0.20)
        if plan and plan.keywords:
            if any(k.lower() in title_lower for k in plan.keywords[:3]):
                score += 0.20
        else:
            # Fallback keyword match
            if any(p in title_lower for p in ["tutorial", "guide", "tips"]):
                score += 0.20

        return min(1.0, score)

    def select_best(self, variants: List[str], plan: Optional[ContentPlan] = None) -> str:
        """Select the highest-scoring title from variants.

        Algorithm: O(n_variants).

        Returns
        -------
        str
            Winning title.
        """
        if not variants:
            return "Untitled Video"
        
        ranked = sorted(
            [(v, self.ctr_score(v, plan)) for v in variants],
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked[0][0]

    def _validate_length(self, title: str, max_len: int = 60) -> str:
        """Trim title to max_len if needed.  O(n)."""
        if len(title) <= max_len:
            return title
        return title[:max_len-3] + "..."
