"""Phase 3 — ThumbnailGenerator: creates SEO-optimized YouTube thumbnails.

Roadmap tasks: T-331 through T-355 (EPIC 3.2 Thumbnail)
Depends on:   Pillow (PIL), ThumbnailScorer, ContentPlan

Algorithm
---------
Generation pipeline:
  1. Select background color (high contrast, CIELAB ΔE > 50)  → O(1)
  2. Load/generate background image (1280×720)                 → O(pixels)
  3. Add title text (bold, 80–100pt, contrast ≥ 4.5:1 WCAG)   → O(glyphs)
  4. Add emoji/icon overlay (attention anchor)                 → O(1)
  5. Apply face detection for person thumbnail (optional)      → O(pixels)
  6. Score via ThumbnailScorer                                 → O(pixels)
  7. Save as JPEG quality=95                                   → O(pixels)

  Target score: ≥ 0.75 (retry if below threshold)

Status: 🔲 Pending — T-331 (Phase 3)
"""
from __future__ import annotations

from pathlib import Path

# TODO: T-331 — implement ThumbnailGenerator class
# TODO: T-332 — implement generate(plan, output_path) → Path
# TODO: T-333 — implement _select_palette(plan) → tuple[RGB, RGB]
# TODO: T-334 — implement _draw_title(img, title) → PIL.Image
# TODO: T-335 — validate score ≥ 0.75 via ThumbnailScorer


class ThumbnailGenerator:
    """TODO: implement in T-331."""

    def generate(self, plan, output_path: Path) -> Path:  # type: ignore[override]
        """TODO: T-332. Returns path to JPEG thumbnail."""
        raise NotImplementedError("T-331 pending")
