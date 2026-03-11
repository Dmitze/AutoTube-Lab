"""Unit tests for ThumbnailScorer (Phase 3, T-149–T-158).

All tests use synthetic images created with numpy/PIL.
No real image files required.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from ytaimbot_ml.seo.thumbnail_scorer import (
    SCORE_THRESHOLD,
    ThumbnailScore,
    ThumbnailScorer,
)


def _create_test_image(
    tmp_path: Path,
    pattern: str = "gradient",
    size: tuple[int, int] = (320, 180),
) -> Path:
    """Create a synthetic test image with PIL.

    Parameters
    ----------
    pattern:
        "gradient" (dark→bright), "flat" (uniform grey), "checkerboard"
    """
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    w, h = size
    if pattern == "gradient":
        # Dark on left, bright on right → good contrast
        data = np.zeros((h, w, 3), dtype=np.uint8)
        for x in range(w):
            v = int(255 * x / w)
            data[:, x, :] = v
    elif pattern == "flat":
        # Uniform grey → low contrast
        data = np.full((h, w, 3), 128, dtype=np.uint8)
    elif pattern == "checkerboard":
        # High edge density
        data = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            for x in range(w):
                data[y, x, :] = 255 if (x // 16 + y // 16) % 2 == 0 else 0
    elif pattern == "colorful":
        # High saturation
        data = np.zeros((h, w, 3), dtype=np.uint8)
        data[:, :w//3, 0] = 255   # Red
        data[:, w//3:2*w//3, 1] = 255  # Green
        data[:, 2*w//3:, 2] = 255  # Blue
    else:
        data = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)

    path = tmp_path / f"test_{pattern}.png"
    Image.fromarray(data).save(str(path))
    return path


class TestThumbnailScore:
    def test_passed_above_threshold(self):
        """ThumbnailScore.passed is True when total >= SCORE_THRESHOLD."""
        s = ThumbnailScore(path="test.png", total=0.7)
        assert s.passed is True

    def test_failed_below_threshold(self):
        """ThumbnailScore.passed is False when total < SCORE_THRESHOLD."""
        s = ThumbnailScore(path="test.png", total=0.3)
        assert s.passed is False

    def test_exactly_threshold(self):
        """ThumbnailScore.passed is True at exact threshold."""
        s = ThumbnailScore(path="test.png", total=SCORE_THRESHOLD)
        assert s.passed is True

    def test_score_threshold_value(self):
        """SCORE_THRESHOLD is 0.5."""
        assert SCORE_THRESHOLD == 0.5


class TestThumbnailScorer:
    def test_returns_thumbnail_score_instance(self, tmp_path):
        """score() returns ThumbnailScore dataclass."""
        scorer = ThumbnailScorer()
        path = _create_test_image(tmp_path, "gradient")
        result = scorer.score(str(path))
        assert isinstance(result, ThumbnailScore)

    def test_total_in_range(self, tmp_path):
        """Total score is in [0, 1]."""
        scorer = ThumbnailScorer()
        path = _create_test_image(tmp_path, "gradient")
        result = scorer.score(str(path))
        assert 0.0 <= result.total <= 1.0

    def test_all_components_in_range(self, tmp_path):
        """All score components are in [0, 1]."""
        scorer = ThumbnailScorer()
        path = _create_test_image(tmp_path, "gradient")
        result = scorer.score(str(path))
        assert 0.0 <= result.contrast <= 1.0
        assert 0.0 <= result.color_energy <= 1.0
        assert 0.0 <= result.edge_density <= 1.0
        assert 0.0 <= result.text_ratio <= 1.0

    def test_gradient_scores_better_than_flat(self, tmp_path):
        """High-contrast gradient scores better than uniform flat image."""
        scorer = ThumbnailScorer()
        gradient = _create_test_image(tmp_path, "gradient")
        flat = _create_test_image(tmp_path, "flat")
        assert scorer.score(str(gradient)).contrast > scorer.score(str(flat)).contrast

    def test_checkerboard_has_high_edges(self, tmp_path):
        """Checkerboard pattern has high edge density."""
        scorer = ThumbnailScorer()
        path = _create_test_image(tmp_path, "checkerboard")
        result = scorer.score(str(path))
        assert result.edge_density > 0.3

    def test_flat_has_low_edges(self, tmp_path):
        """Uniform image has low edge density."""
        scorer = ThumbnailScorer()
        path = _create_test_image(tmp_path, "flat")
        result = scorer.score(str(path))
        assert result.edge_density < 0.3

    def test_missing_file_returns_neutral(self):
        """Non-existent file returns neutral score (0.5) without crash."""
        scorer = ThumbnailScorer()
        result = scorer.score("/nonexistent/path.png")
        assert result.total == 0.5
        assert result.path == "/nonexistent/path.png"

    def test_path_stored_in_result(self, tmp_path):
        """Result.path matches input path."""
        scorer = ThumbnailScorer()
        path = _create_test_image(tmp_path, "flat")
        result = scorer.score(str(path))
        assert result.path == str(path)

    def test_deterministic(self, tmp_path):
        """Same image scores identically on repeated calls."""
        scorer = ThumbnailScorer()
        path = _create_test_image(tmp_path, "gradient")
        r1 = scorer.score(str(path))
        r2 = scorer.score(str(path))
        assert r1.total == r2.total

    def test_colorful_has_color_energy(self, tmp_path):
        """Highly saturated image has high color_energy."""
        scorer = ThumbnailScorer()
        path = _create_test_image(tmp_path, "colorful")
        result = scorer.score(str(path))
        # Colorful image should have higher energy than flat grey
        flat = _create_test_image(tmp_path, "flat")
        flat_result = scorer.score(str(flat))
        assert result.color_energy >= flat_result.color_energy
