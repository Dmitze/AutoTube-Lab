"""Phase 3 — Video adapters sub-package.

Adapters
--------
VideoAssembler  : MoviePy + FFmpeg pipeline (clips → final MP4)
ThumbnailGen    : Pillow 1280×720 thumbnail generator
SubtitleGen     : SRT/ASS subtitle generator + FFmpeg burn-in

Output:
  videos/  : final MP4 (1080p, H.264, AAC)
  thumbnails/ : JPEG 1280×720

Status: 🔲 Pending — T-300 (Phase 3, EPIC 3.1)
"""
