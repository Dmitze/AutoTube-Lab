"""Tests for OpenSoraGenerator and create_video_backend factory (T-426–T-428).

All GPU calls are mocked — no real GPU or Open-Sora required.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modules.adapters.video.ai_generator import (
    OpenSoraGenerator,
    create_video_backend,
)
from modules.adapters.video.assembler import VideoAssembler


# ---------------------------------------------------------------------------
# T-427: GPU unavailable → fallback to MoviePy
# ---------------------------------------------------------------------------

def test_create_video_backend_no_gpu_returns_moviepy(tmp_path):
    """T-427: When GPU is unavailable, create_video_backend returns VideoAssembler."""
    backend = create_video_backend(
        use_open_sora=True,
        gpu_available=False,  # explicitly no GPU
        output_dir=tmp_path,
    )
    assert isinstance(backend, VideoAssembler), (
        f"Expected VideoAssembler, got {type(backend).__name__}"
    )


def test_create_video_backend_torch_unavailable_returns_moviepy(tmp_path):
    """T-427: When torch is not installed, falls back to MoviePy."""
    with patch.dict("sys.modules", {"torch": None}):
        backend = create_video_backend(
            use_open_sora=True,
            gpu_available=None,  # auto-detect (will fail without torch)
            output_dir=tmp_path,
        )
    assert isinstance(backend, VideoAssembler)


def test_create_video_backend_gpu_available_returns_sora(tmp_path):
    """T-427: When GPU is available and USE_OPEN_SORA=true, returns OpenSoraGenerator."""
    backend = create_video_backend(
        use_open_sora=True,
        gpu_available=True,
        output_dir=tmp_path,
    )
    assert isinstance(backend, OpenSoraGenerator)


# ---------------------------------------------------------------------------
# T-428: USE_OPEN_SORA=false → MoviePy regardless of GPU
# ---------------------------------------------------------------------------

def test_create_video_backend_sora_disabled_returns_moviepy(tmp_path):
    """T-428: USE_OPEN_SORA=false always returns VideoAssembler."""
    backend = create_video_backend(
        use_open_sora=False,
        gpu_available=True,  # GPU available but Sora disabled
        output_dir=tmp_path,
    )
    assert isinstance(backend, VideoAssembler)


def test_create_video_backend_default_is_moviepy(tmp_path):
    """T-428: Default call (no args) returns VideoAssembler."""
    backend = create_video_backend(output_dir=tmp_path)
    assert isinstance(backend, VideoAssembler)


# ---------------------------------------------------------------------------
# T-422: GPU availability check
# ---------------------------------------------------------------------------

def test_gpu_check_uses_torch_cuda(tmp_path):
    """T-422: GPU check calls torch.cuda.is_available() when torch is present."""
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False

    with patch.dict("sys.modules", {"torch": mock_torch}):
        backend = create_video_backend(
            use_open_sora=True,
            gpu_available=None,  # auto-detect
            output_dir=tmp_path,
        )

    mock_torch.cuda.is_available.assert_called_once()
    assert isinstance(backend, VideoAssembler)  # no GPU → MoviePy


# ---------------------------------------------------------------------------
# T-420: OpenSoraGenerator stub raises NotImplementedError on CPU
# ---------------------------------------------------------------------------

def test_open_sora_generator_raises_on_cpu():
    """T-420: OpenSoraGenerator.generate() raises NotImplementedError (CPU stub)."""
    gen = OpenSoraGenerator(model="open-sora-v1")
    with pytest.raises(NotImplementedError):
        gen.generate(prompt="A cozy Ghibli cabin in winter", duration=5)


def test_open_sora_generator_model_attribute():
    """T-420: OpenSoraGenerator stores model name."""
    gen = OpenSoraGenerator(model="open-sora-v2")
    assert gen.model == "open-sora-v2"
