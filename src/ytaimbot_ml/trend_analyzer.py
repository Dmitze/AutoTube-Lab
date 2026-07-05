"""Trend analyzer — PCA-based dimensionality reduction and ranking.

Complexity notes
----------------
fit_transform : O(min(n, d) * n * d)  where n = samples, d = features
score_trends  : O(n log n)             sorting by vector magnitude
analyze       : O(min(n, d) * n * d + n log n)
"""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import TruncatedSVD

from ytaimbot_ml.schemas import TrendRanking, TrendSignal


class TrendAnalyzer:
    """MVP trend analyzer using SVD/PCA for dimensionality reduction.

    Parameters
    ----------
    rng:
        Optional seeded NumPy random generator for reproducibility.
        Pass ``np.random.default_rng(42)`` to obtain deterministic results.
    """

    def __init__(self, rng: np.random.Generator | None = None) -> None:
        self._rng = rng if rng is not None else np.random.default_rng()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit_transform(self, X: np.ndarray, n_components: int) -> np.ndarray:
        """Reduce feature matrix via truncated SVD.

        Complexity: O(min(n, d) * n * d) where n = rows, d = columns.

        Parameters
        ----------
        X:
            2-D array of shape (n_samples, n_features).
        n_components:
            Target number of dimensions (must be < min(n_samples, n_features)).

        Returns
        -------
        np.ndarray
            Reduced array of shape (n_samples, n_components).
        """
        n_components = min(n_components, min(X.shape) - 1)
        # TruncatedSVD is deterministic given the same random_state seed
        seed_int = int(self._rng.integers(0, 2**31))
        svd = TruncatedSVD(n_components=n_components, random_state=seed_int)
        return svd.fit_transform(X)

    def score_trends(
        self, reduced: np.ndarray, trend_ids: list[str]
    ) -> list[TrendRanking]:
        """Rank trends by L2 magnitude of their reduced feature vectors.

        Complexity: O(n log n) where n = number of trends.

        Parameters
        ----------
        reduced:
            2-D array of shape (n_trends, n_components).
        trend_ids:
            List of trend IDs matching the row order of ``reduced``.

        Returns
        -------
        list[TrendRanking]
            Rankings sorted in descending order (highest score first).
        """
        magnitudes = np.linalg.norm(reduced, axis=1)
        ranked = sorted(
            zip(trend_ids, magnitudes),
            key=lambda x: x[1],
            reverse=True,
        )
        return [TrendRanking(trend_id=tid, score=float(score)) for tid, score in ranked]

    def analyze(
        self, signals: list[TrendSignal], n_components: int = 2,
        feedback_scorer=None
    ) -> list[TrendRanking]:
        """Full pipeline: featurize → reduce → score.

        Complexity: O(min(n, d) * n * d + n log n).

        Parameters
        ----------
        signals:
            Raw trend signals to analyse.
        n_components:
            Number of PCA components to retain.
        feedback_scorer:
            Optional FeedbackScorer to adjust weights based on metrics.

        Returns
        -------
        list[TrendRanking]
            Sorted rankings for all input signals.
        """
        if not signals:
            return []

        feature_matrix = self._featurize(signals)
        trend_ids = [s.trend_id for s in signals]

        if feature_matrix.shape[1] <= n_components:
            # Not enough features to reduce — fall back to raw magnitude ranking
            rankings = self.score_trends(feature_matrix, trend_ids)
        else:
            reduced = self.fit_transform(feature_matrix, n_components)
            rankings = self.score_trends(reduced, trend_ids)

        if feedback_scorer is not None:
            weights = feedback_scorer.get_weights()
            signal_map = {s.trend_id: s.keyword for s in signals}
            for rank in rankings:
                niche = signal_map.get(rank.trend_id, "")
                weight = weights.get(niche, 1.0)
                rank.score *= weight
            
            # Re-sort after weighting
            rankings.sort(key=lambda x: x.score, reverse=True)

        return rankings

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _featurize(signals: list[TrendSignal]) -> np.ndarray:
        """Convert TrendSignal list to a numeric feature matrix.

        Currently uses raw_score as the primary feature dimension plus a
        hash-derived secondary feature so the matrix is always 2-D.
        """
        rows: list[list[float]] = []
        for sig in signals:
            # Feature 0: raw_score (primary signal strength)
            # Feature 1: hash-derived noise proxy (stable across runs)
            hash_val = int(hash(sig.keyword) & 0xFFFF) / 0xFFFF
            rows.append([sig.raw_score, hash_val])
        return np.array(rows, dtype=float)


# ---------------------------------------------------------------------------
# Module entry-point for quick sanity check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from ytaimbot_ml.utils.random import make_rng

    rng = make_rng(42)
    analyzer = TrendAnalyzer(rng=rng)

    demo_signals = [
        TrendSignal(
            trend_id=f"t{i}",
            keyword=f"keyword_{i}",
            raw_score=float(i),
            source="demo",
            timestamp="2026-01-01T00:00:00Z",
        )
        for i in range(5)
    ]

    rankings = analyzer.analyze(demo_signals)
    for rank in rankings:
        print(f"  {rank.trend_id}: {rank.score:.4f}")
