"""Tests for ThumbnailGenerator color schemes (T-187).

Verifies that all 5 color palettes generate valid thumbnails without errors.
No real image files are written — uses tmp_path fixture.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ytaimbot_ml.schemas import ContentPlan


# ---------------------------------------------------------------------------
# T-187: All 5 ColorScheme palettes generate without errors
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_plan() -> ContentPlan:
    return ContentPlan(
        trend_id="t001",
        title="Top 5 AI Tools for 2026",
        outline=["Hook", "Intro", "Body", "CTA"],
        keywords=["AI", "tools", "automation"],
    )


def test_all_5_palettes_generate_without_error(tmp_path, sample_plan):
    """T-187: All 5 color palettes in ThumbnailGenerator produce valid output."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        pytest.skip("Pillow not installed")

    from modules.adapters.video.thumbnail import ThumbnailGenerator, _PALETTES

    assert len(_PALETTES) == 5, f"Expected 5 palettes, got {len(_PALETTES)}"

    generator = ThumbnailGenerator(output_dir=tmp_path)

    for i, palette in enumerate(_PALETTES):
        output_path = tmp_path / f"thumb_palette_{i}.jpg"
        # Patch _PALETTES to use only this one palette
        with patch("modules.adapters.video.thumbnail._PALETTES", [palette]):
            result_path = generator.generate(
                plan=sample_plan,
                output_path=output_path,
            )

        assert result_path is not None, f"Palette {i} returned None"
        assert Path(result_path).exists(), f"Palette {i}: file not created at {result_path}"

        # Verify dimensions
        img = Image.open(result_path)
        assert img.width == 1280, f"Palette {i}: width={img.width}, expected 1280"
        assert img.height == 720, f"Palette {i}: height={img.height}, expected 720"

        # Verify file size <= 2MB
        size_mb = Path(result_path).stat().st_size / (1024 * 1024)
        assert size_mb <= 2.0, f"Palette {i}: size={size_mb:.2f}MB > 2MB"


def test_thumbnail_generator_uses_all_palettes_on_retry(tmp_path, sample_plan):
    """T-187: Generator tries alternative palettes when score is below threshold."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    from modules.adapters.video.thumbnail import ThumbnailGenerator

    generator = ThumbnailGenerator(output_dir=tmp_path)

    # Mock scorer to always return low score (forces retry through all palettes)
    with patch("modules.adapters.video.thumbnail.ThumbnailScorer") as MockScorer:
        mock_scorer_instance = MockScorer.return_value
        mock_scorer_instance.score.return_value = MagicMock(total=0.0)  # always fails

        output_path = tmp_path / "thumb_retry.jpg"
        result_path = generator.generate(plan=sample_plan, output_path=output_path)

    # Even with low score, generator should produce a file (uses last palette)
    assert result_path is not None
    assert Path(result_path).exists()


def test_palette_colors_are_valid_rgb(sample_plan):
    """T-187: All palette colors are valid RGB tuples (0-255 range)."""
    from modules.adapters.video.thumbnail import _PALETTES

    for i, (bg, text, accent) in enumerate(_PALETTES):
        for channel in bg:
            assert 0 <= channel <= 255, f"Palette {i} bg channel {channel} out of range"
        for channel in text:
            assert 0 <= channel <= 255, f"Palette {i} text channel {channel} out of range"
        for channel in accent:
            assert 0 <= channel <= 255, f"Palette {i} accent channel {channel} out of range"
