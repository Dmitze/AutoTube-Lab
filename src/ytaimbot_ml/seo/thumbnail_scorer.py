"""Phase 3 — ThumbnailScorer: CTR-optimized thumbnail quality scoring.

Roadmap tasks: T-149 through T-158 (EPIC 3.2 Thumbnail)
Depends on:   Pillow (PIL) — optional; graceful degradation if missing

Algorithms
----------
1. Contrast score (Weber's Law approximation):
     contrast = |L_foreground - L_background| / max(L_background, 1)
     Normalized to [0, 1]. O(pixels).

2. Text area ratio:
     text_ratio = bright_pixel_count / total_pixels
     Proxy for text presence (high-contrast regions). O(pixels).

3. Color energy (saturation):
     energy = mean(saturation channel in HSV)
     High saturation → more eye-catching thumbnails. O(pixels).

4. Edge density (sharpness proxy):
     edge_density = non-zero Sobel edges / total_pixels
     Sharp thumbnails with clear subjects score higher. O(pixels).

5. Composite score:
     score = 0.35 × contrast
           + 0.25 × color_energy
           + 0.25 × edge_density
           + 0.15 × text_ratio

   All components in [0, 1]. Total in [0, 1]. O(pixels).

Note: Full face detection (OpenCV Haar cascade) deferred to Phase 5
because it requires OpenCV binary. Stubbed here as face_score=0.5 baseline.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Composite score weights
_W_CONTRAST = 0.35
_W_COLOR    = 0.25
_W_EDGE     = 0.25
_W_TEXT     = 0.15

# Minimum acceptable thumbnail score for publishing
SCORE_THRESHOLD = 0.5


@dataclass
class ThumbnailScore:
    """Detailed quality score breakdown for a thumbnail.

    Attributes
    ----------
    path:
        Path to the evaluated image.
    total:
        Composite score in [0, 1].
    contrast:
        Luminance contrast score in [0, 1].
    color_energy:
        Mean saturation in [0, 1].
    edge_density:
        Sharpness proxy in [0, 1].
    text_ratio:
        High-contrast pixel ratio in [0, 1].
    passed:
        True if total >= SCORE_THRESHOLD.
    """

    path: str
    total: float = 0.0
    contrast: float = 0.0
    color_energy: float = 0.0
    edge_density: float = 0.0
    text_ratio: float = 0.0

    @property
    def passed(self) -> bool:
        """True if thumbnail meets minimum quality threshold."""
        return self.total >= SCORE_THRESHOLD


class ThumbnailScorer:
    """Scores thumbnail images for CTR potential.

    Requires Pillow (``pip install Pillow``).
    Falls back to a neutral score of 0.5 if Pillow is unavailable.

    Parameters
    ----------
    target_size:
        Expected image dimensions (width, height). Default: (1280, 720).

    Complexity
    ----------
    score(): O(pixels) — dominated by pixel-level operations

    Examples
    --------
    >>> scorer = ThumbnailScorer()
    >>> isinstance(scorer, ThumbnailScorer)
    True
    """

    def __init__(self, target_size: tuple[int, int] = (1280, 720)) -> None:
        self.target_size = target_size

    def score(self, image_path: str | Path) -> ThumbnailScore:
        """Score a thumbnail image.

        Parameters
        ----------
        image_path:
            Path to the thumbnail image (PNG or JPG).

        Returns
        -------
        ThumbnailScore
            Detailed score breakdown. Falls back to neutral (0.5) if
            Pillow is unavailable or image cannot be read.

        Complexity
        ----------
        O(W × H) — pixel-level processing

        Examples
        --------
        >>> scorer = ThumbnailScorer()
        >>> result = scorer.score("nonexistent.png")
        >>> 0.0 <= result.total <= 1.0
        True
        """
        path_str = str(image_path)

        try:
            from PIL import Image  # noqa: PLC0415
            import numpy as np    # noqa: PLC0415
        except ImportError:
            logger.warning("Pillow not installed — returning neutral thumbnail score")
            return ThumbnailScore(path=path_str, total=0.5, contrast=0.5,
                                  color_energy=0.5, edge_density=0.5, text_ratio=0.5)

        try:
            img = Image.open(path_str).convert("RGB")
        except (FileNotFoundError, OSError) as exc:
            logger.warning("Cannot open thumbnail %s: %s", path_str, exc)
            return ThumbnailScore(path=path_str, total=0.5, contrast=0.5,
                                  color_energy=0.5, edge_density=0.5, text_ratio=0.5)

        pixels = np.array(img, dtype=np.float32)  # shape: (H, W, 3)

        contrast  = self._contrast_score(pixels)
        color     = self._color_energy(pixels)
        edges     = self._edge_density(pixels)
        text_r    = self._text_ratio(pixels)

        total = (
            _W_CONTRAST * contrast
            + _W_COLOR   * color
            + _W_EDGE    * edges
            + _W_TEXT    * text_r
        )

        return ThumbnailScore(
            path=path_str,
            total=round(total, 4),
            contrast=round(contrast, 4),
            color_energy=round(color, 4),
            edge_density=round(edges, 4),
            text_ratio=round(text_r, 4),
        )

    # ------------------------------------------------------------------
    # Private scoring components — each returns float in [0, 1]
    # ------------------------------------------------------------------

    @staticmethod
    def _contrast_score(pixels: "np.ndarray") -> float:  # type: ignore[name-defined]
        """Luminance contrast between bright and dark regions. O(pixels).

        Algorithm: split pixels into top/bottom luminance quartiles,
        compute Weber contrast = (L_bright - L_dark) / (L_dark + 1).
        Normalized to [0, 1] via sigmoid approximation.

        Parameters
        ----------
        pixels:
            Float32 RGB array of shape (H, W, 3).

        Returns
        -------
        float
            Contrast score in [0, 1].
        """
        import numpy as np  # noqa: PLC0415
        # Perceived luminance (ITU-R BT.601)
        luminance = (
            0.299 * pixels[:, :, 0]
            + 0.587 * pixels[:, :, 1]
            + 0.114 * pixels[:, :, 2]
        ) / 255.0  # normalize to [0, 1]

        flat = luminance.flatten()
        q25 = float(np.percentile(flat, 25))
        q75 = float(np.percentile(flat, 75))
        weber = (q75 - q25) / (q25 + 0.01)
        return min(1.0, weber / 3.0)  # normalize: 3.0 ≈ high contrast

    @staticmethod
    def _color_energy(pixels: "np.ndarray") -> float:  # type: ignore[name-defined]
        """Mean HSV saturation as a proxy for visual vibrancy. O(pixels).

        Parameters
        ----------
        pixels:
            Float32 RGB array of shape (H, W, 3).

        Returns
        -------
        float
            Mean saturation in [0, 1].
        """
        from PIL import Image  # noqa: PLC0415
        import numpy as np    # noqa: PLC0415
        # Convert to HSV via PIL
        rgb_uint8 = pixels.astype("uint8")
        img_hsv = Image.fromarray(rgb_uint8).convert("HSV")
        hsv = np.array(img_hsv, dtype=np.float32)
        # Saturation = channel 1 of HSV, PIL range [0, 255]
        mean_sat = float(np.mean(hsv[:, :, 1])) / 255.0
        return min(1.0, mean_sat)

    @staticmethod
    def _edge_density(pixels: "np.ndarray") -> float:  # type: ignore[name-defined]
        """Sharpness proxy via Sobel gradient magnitude. O(pixels).

        Uses a simplified 3×3 Sobel without scipy/cv2 dependency.

        Parameters
        ----------
        pixels:
            Float32 RGB array of shape (H, W, 3).

        Returns
        -------
        float
            Edge density in [0, 1].
        """
        import numpy as np  # noqa: PLC0415
        gray = (
            0.299 * pixels[:, :, 0]
            + 0.587 * pixels[:, :, 1]
            + 0.114 * pixels[:, :, 2]
        ) / 255.0

        # Sobel-X and Sobel-Y (manual convolution with numpy slicing)
        gx = gray[1:-1, 2:] - gray[1:-1, :-2]   # horizontal gradient
        gy = gray[2:, 1:-1] - gray[:-2, 1:-1]   # vertical gradient
        magnitude = np.sqrt(gx**2 + gy**2)
        density = float(np.mean(magnitude > 0.1))  # fraction of strong edges
        return min(1.0, density * 4.0)  # scale: ~25% edges → score 1.0

    @staticmethod
    def _text_ratio(pixels: "np.ndarray") -> float:  # type: ignore[name-defined]
        """Ratio of near-white or near-black pixels (text proxy). O(pixels).

        High-contrast text creates clusters of very bright or very dark pixels.

        Parameters
        ----------
        pixels:
            Float32 RGB array of shape (H, W, 3).

        Returns
        -------
        float
            Text ratio in [0, 1].
        """
        import numpy as np  # noqa: PLC0415
        luminance = (
            0.299 * pixels[:, :, 0]
            + 0.587 * pixels[:, :, 1]
            + 0.114 * pixels[:, :, 2]
        ) / 255.0
        bright = float(np.mean(luminance > 0.85))  # near-white
        dark   = float(np.mean(luminance < 0.15))  # near-black
        ratio  = bright + dark
        return min(1.0, ratio * 3.0)  # scale: ~33% text pixels → score 1.0

