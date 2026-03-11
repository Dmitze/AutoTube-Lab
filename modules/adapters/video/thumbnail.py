"""Phase 4 — ThumbnailGenerator: creates SEO-optimized YouTube thumbnails.

Roadmap tasks: T-196 through T-205 (EPIC 4.2 Thumbnail)
Depends on:   Pillow (PIL), ThumbnailScorer, ContentPlan

Generation pipeline:
  1. Select color palette (high-contrast pair)   → O(1) dict lookup
  2. Create 1280×720 gradient background         → O(pixels)
  3. Draw title text (bold, white/yellow)        → O(glyphs)
  4. Add accent bar (colored bottom strip)       → O(1)
  5. Score via ThumbnailScorer                   → O(pixels)
  6. Export PNG quality=95                       → O(pixels)

Target score: ≥ 0.5 (SCORE_THRESHOLD)
Retry: if score < threshold, try alternative palette.

Complexity: O(W × H) = O(1280 × 720) ≈ O(1M pixels)
"""
from __future__ import annotations

import logging
from pathlib import Path

from ytaimbot_ml.schemas import ContentPlan
from ytaimbot_ml.seo.thumbnail_scorer import SCORE_THRESHOLD, ThumbnailScorer

logger = logging.getLogger(__name__)

# Output dimensions
THUMB_WIDTH = 1280
THUMB_HEIGHT = 720

# Color palettes: (background_color, text_color, accent_color)
_PALETTES: list[tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]] = [
    ((15, 15, 35),    (255, 255, 0),   (255, 80, 0)),    # Dark navy + yellow + orange
    ((200, 0, 0),     (255, 255, 255), (255, 200, 0)),   # Red + white + gold
    ((0, 60, 120),    (255, 220, 0),   (0, 200, 100)),   # Navy + yellow + green
    ((20, 20, 20),    (255, 255, 255), (0, 160, 255)),   # Dark + white + blue
    ((50, 0, 80),     (255, 255, 255), (255, 120, 0)),   # Purple + white + orange
]


class ThumbnailGenerator:
    """Generates YouTube thumbnails with high CTR potential.

    Parameters
    ----------
    output_dir:
        Directory for thumbnail PNG files.
    width:
        Thumbnail width in pixels (default 1280).
    height:
        Thumbnail height in pixels (default 720).

    Complexity
    ----------
    generate(): O(W × H) — pixel-level Pillow operations

    Examples
    --------
    >>> gen = ThumbnailGenerator(output_dir="/tmp")
    >>> gen.width
    1280
    """

    def __init__(
        self,
        output_dir: str | Path = "data/thumbnails",
        width: int = THUMB_WIDTH,
        height: int = THUMB_HEIGHT,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.width = width
        self.height = height
        self._scorer = ThumbnailScorer(target_size=(width, height))

    def generate(self, plan: ContentPlan, output_path: Path | None = None) -> Path:
        """Generate a thumbnail for a ContentPlan.

        Parameters
        ----------
        plan:
            ContentPlan with title and keywords.
        output_path:
            Destination PNG path. Auto-generated from plan_id if None.

        Returns
        -------
        Path
            Path to the generated PNG file.

        Raises
        ------
        ImportError
            If Pillow is not installed.

        Complexity
        ----------
        O(W × H) — Pillow pixel operations

        Examples
        --------
        >>> from ytaimbot_ml.schemas import ContentPlan
        >>> plan = ContentPlan("t1", "Python Tutorial", [], ["python"])
        >>> gen = ThumbnailGenerator(output_dir="/tmp")
        >>> path = gen.generate(plan)  # doctest: +SKIP
        """
        try:
            from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError("Pillow not installed: pip install Pillow") from exc

        self.output_dir.mkdir(parents=True, exist_ok=True)
        if output_path is None:
            output_path = self.output_dir / f"{plan.trend_id}_thumb.png"

        best_path: Path | None = None
        best_score: float = -1.0

        # Try each palette; keep the one with best ThumbnailScorer score
        for i, (bg, fg, accent) in enumerate(_PALETTES):
            candidate = self.output_dir / f"{plan.trend_id}_thumb_v{i}.png"
            self._render(plan.title, bg, fg, accent, candidate, ImageDraw, Image, ImageFont)
            score = self._scorer.score(str(candidate)).total
            logger.debug("Thumbnail palette %d → score=%.3f", i, score)
            if score > best_score:
                best_score = score
                best_path = candidate
            if score >= SCORE_THRESHOLD:
                break

        # Copy best to final path
        import shutil  # noqa: PLC0415
        shutil.copy2(str(best_path), str(output_path))

        # Clean up candidate files
        for i in range(len(_PALETTES)):
            candidate = self.output_dir / f"{plan.trend_id}_thumb_v{i}.png"
            if candidate.exists() and candidate != output_path:
                candidate.unlink(missing_ok=True)

        logger.info(
            "ThumbnailGenerator: %s → score=%.3f path=%s",
            plan.trend_id,
            best_score,
            output_path,
        )
        return output_path

    def _render(
        self,
        title: str,
        bg_color: tuple[int, int, int],
        text_color: tuple[int, int, int],
        accent_color: tuple[int, int, int],
        output_path: Path,
        ImageDraw,
        Image,
        ImageFont,
    ) -> None:
        """Render a single thumbnail variant. O(W × H).

        Layout:
          - Gradient background (bg_color → darker)
          - Bold title text (centered, wrapped at 30 chars/line)
          - Accent bar at bottom (20px, accent_color)
        """
        img = Image.new("RGB", (self.width, self.height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Gradient overlay (darken left side)
        import numpy as np  # noqa: PLC0415
        pixels = np.array(img, dtype=np.float32)
        for x in range(self.width):
            factor = 0.6 + 0.4 * (x / self.width)  # left: 60%, right: 100%
            pixels[:, x, :] *= factor
        img = Image.fromarray(pixels.clip(0, 255).astype("uint8"))
        draw = ImageDraw.Draw(img)

        # Title text (try to use a system font, fall back to default)
        font_size = 72
        font = self._load_font(ImageFont, font_size)

        # Wrap title at ~25 chars per line
        words = title.split()
        lines: list[str] = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= 25:
                current = f"{current} {word}".strip()
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        # Center text block vertically
        line_height = font_size + 10
        total_height = len(lines) * line_height
        y_start = (self.height - total_height) // 2

        for j, line in enumerate(lines):
            # Shadow
            draw.text((self.width // 2 + 3, y_start + j * line_height + 3),
                      line, fill=(0, 0, 0), font=font, anchor="mm")
            # Main text
            draw.text((self.width // 2, y_start + j * line_height),
                      line, fill=text_color, font=font, anchor="mm")

        # Accent bar at bottom
        draw.rectangle(
            [(0, self.height - 20), (self.width, self.height)],
            fill=accent_color,
        )

        img.save(str(output_path), format="PNG", optimize=True)

    @staticmethod
    def _load_font(ImageFont, size: int):
        """Try system fonts, fall back to Pillow default. O(1)."""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
        ]
        for fp in font_paths:
            try:
                return ImageFont.truetype(fp, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

