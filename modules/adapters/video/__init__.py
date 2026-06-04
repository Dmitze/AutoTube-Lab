"""Phase 3 — Video adapters sub-package."""

from __future__ import annotations

from modules.adapters.video.assembler import VideoAssembler
from modules.adapters.video.kling import KlingAdapter
from modules.adapters.video.pexels import PexelsStockAdapter, StockVideo
from modules.adapters.video.subtitle import SubtitleGenerator
from modules.adapters.video.thumbnail import ThumbnailGenerator
from modules.adapters.video.ai_generator import create_video_backend

__all__ = [
    "VideoAssembler",
    "ThumbnailGenerator",
    "SubtitleGenerator",
    "PexelsStockAdapter",
    "StockVideo",
    "KlingAdapter",
    "create_video_backend",
]
