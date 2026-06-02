"""Phase 4 — SimilarityGate: plagiarism and duplicate content detection.

Roadmap tasks: T-269 through T-280 (EPIC 4.3 Similarity Gate)

Algorithm
---------
1. Vectorization: TF-IDF bag-of-words (O(vocab))
2. Comparison: Cosine similarity between new script and archive (O(vocab * n_archive))
3. Decision: Pass if max similarity < THRESHOLD (0.85)

Note: In Phase 6+, we might move to Dense Embeddings (SBERT) + ANN for scale.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SimilarityReport:
    """Result of a content similarity check."""
    score: float
    decision: Literal["pass", "block"]
    content_hash: str
    matches: List[str]  # IDs of archived videos that matched


class SimilarityGate:
    """Plagiarism guard using TF-IDF and Cosine Similarity.

    Parameters
    ----------
    threshold:
        Similarity score above which content is blocked (default 0.85).
    """

    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold
        # Simple stop words for O(1) filtering
        self._stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}

    def check(self, new_text: str, archive: Dict[str, str]) -> SimilarityReport:
        """Check if new_text is too similar to any archived content.

        Algorithm: TF-IDF Cosine Similarity proxy — O(vocab * n_archive).

        Parameters
        ----------
        new_text:
            The new script or content to verify.
        archive:
            Dictionary of {video_id: script_text}.

        Returns
        -------
        SimilarityReport
            Decision and matching scores.
        """
        if not archive:
            return SimilarityReport(
                score=0.0,
                decision="pass",
                content_hash=self.get_hash(new_text),
                matches=[],
            )

        new_vec = self._vectorize(new_text)
        max_sim = 0.0
        matches = []

        for vid, text in archive.items():
            arch_vec = self._vectorize(text)
            sim = self._cosine_sim(new_vec, arch_vec)
            if sim > max_sim:
                max_sim = sim
            if sim > self.threshold:
                matches.append(vid)

        decision = "block" if max_sim > self.threshold else "pass"
        
        logger.debug(
            "SimilarityGate: max_sim=%.2f decision=%s (archive_size=%d)",
            max_sim,
            decision,
            len(archive),
        )

        return SimilarityReport(
            score=max_sim,
            decision=decision,
            content_hash=self.get_hash(new_text),
            matches=matches,
        )

    def get_hash(self, text: str) -> str:
        """Compute SHA-256 hash of normalized text.  O(n)."""
        norm = self._normalize(text)
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    def _normalize(self, text: str) -> str:
        """Clean text for vectorization.  O(n)."""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        return text

    def _vectorize(self, text: str) -> Dict[str, float]:
        """Convert text to TF-IDF-like bag-of-words vector.  O(n)."""
        words = self._normalize(text).split()
        counts: Dict[str, int] = {}
        for w in words:
            if w not in self._stop_words:
                counts[w] = counts.get(w, 0) + 1
        
        # Simple L2 normalization for the vector
        norm = np.sqrt(sum(c*c for c in counts.values()))
        if norm == 0:
            return {}
        
        return {w: c / norm for w, c in counts.items()}

    def _cosine_sim(self, v1: Dict[str, float], v2: Dict[str, float]) -> float:
        """Compute cosine similarity between two sparse vectors.  O(vocab)."""
        # Since vectors are pre-normalized, dot product = cosine similarity
        score = 0.0
        # Iterate over smaller vector for efficiency
        if len(v1) > len(v2):
            v1, v2 = v2, v1
        
        for word, val1 in v1.items():
            if word in v2:
                score += val1 * v2[word]
        
        return score
