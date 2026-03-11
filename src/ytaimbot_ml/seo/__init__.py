"""Phase 3 — SEO optimization package.

Public API
----------
TitleOptimizer    : CTR-scored title generation (template bank + scoring)
TitleScore        : Dataclass with per-component score breakdown
ThumbnailScorer   : Pillow-based thumbnail quality scoring
ThumbnailScore    : Dataclass with per-component score breakdown
SCORE_THRESHOLD   : Minimum thumbnail score for publishing (0.5)

Algorithms
----------
Title scoring:     O(1) weighted formula (keyword, length, power words)
Template matching: O(n_templates) argmax
Thumbnail scoring: O(W × H) pixel-level Sobel + luminance + saturation
"""
from ytaimbot_ml.seo.title_optimizer import TitleOptimizer, TitleScore
from ytaimbot_ml.seo.thumbnail_scorer import SCORE_THRESHOLD, ThumbnailScore, ThumbnailScorer

__all__ = [
    "TitleOptimizer",
    "TitleScore",
    "ThumbnailScorer",
    "ThumbnailScore",
    "SCORE_THRESHOLD",
]

