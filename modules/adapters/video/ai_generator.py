"""Phase 6 — OpenSoraGenerator: GPU-gated AI video generation stub.

Roadmap tasks: T-420 through T-428 (EPIC 6.4 Open-Sora Integration)
Dependencies:  torch (optional), moviepy (fallback)

Algorithm
---------
1. GPU Check (T-422): 
   Verify torch.cuda.is_available().
   O(1) check.

2. Fallback (T-424):
   If GPU unavailable or Open-Sora not installed, return MoviePyAssembler.
   O(1) selection.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from modules.adapters.video.assembler import VideoAssembler
from ytaimbot_ml.schemas import Script, VideoAsset

logger = logging.getLogger(__name__)


class OpenSoraGenerator:
    """AI video generator using Open-Sora (stub).

    Currently a stub that falls back to MoviePy unless GPU is present
    and USE_OPEN_SORA=true.
    """

    def __init__(self, model: str = "open-sora-v1") -> None:
        self.model = model

    def generate(self, prompt: str, duration: int) -> Path:
        """Stub for AI video generation. O(1) stub."""
        logger.info("OpenSoraGenerator: generating video for prompt '%s'", prompt[:50])
        # In a real implementation, this would call the Open-Sora model
        # For now, we return a fake path or raise if called in CPU mode
        raise NotImplementedError("OpenSoraGenerator is not implemented for CPU")


def create_video_backend(
    use_open_sora: bool = False,
    gpu_available: Optional[bool] = None,
    sora_model: str = "open-sora-v1",
    output_dir: str | Path = "data/videos",
) -> VideoAssembler | OpenSoraGenerator:
    """Factory function with GPU gate (T-423).

    Complexity: O(1).
    """
    if gpu_available is None:
        try:
            import torch
            gpu_available = torch.cuda.is_available()
        except ImportError:
            gpu_available = False

    if use_open_sora and gpu_available:
        logger.info("VideoBackend: using OpenSoraGenerator (GPU detected)")
        return OpenSoraGenerator(model=sora_model)

    logger.info("VideoBackend: using MoviePyAssembler (CPU mode)")
    return VideoAssembler(output_dir=output_dir)
