"""Unit tests for CoquiTTSAdapter (T-395).

Tests the graceful-fallback implementation: silent WAV when coqui-tts
is not installed, full synthesis when available.

Coverage:
  test_coqui_is_available
  test_coqui_synthesize_creates_file
  test_coqui_synthesize_returns_path
  test_coqui_list_models_no_lib
  test_coqui_default_model_name
  test_coqui_custom_output_path
  test_coqui_silent_wav_is_valid
  test_coqui_constructor_params
"""
from __future__ import annotations

import os
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modules.adapters.tts.coqui_tts import CoquiTTSAdapter


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


def test_coqui_is_available() -> None:
    """is_available is False in test env (coqui-tts not installed)."""
    adapter = CoquiTTSAdapter()
    # is_available is a property, must return bool
    assert isinstance(adapter.is_available, bool)
    # In the CI/test environment coqui-tts is NOT installed
    with patch("modules.adapters.tts.coqui_tts._COQUI_AVAILABLE", False):
        adapter2 = CoquiTTSAdapter()
        assert adapter2.is_available is False


# ---------------------------------------------------------------------------
# Default model name
# ---------------------------------------------------------------------------


def test_coqui_default_model_name() -> None:
    """Default model is the tacotron2-DDC English model."""
    adapter = CoquiTTSAdapter()
    assert adapter.DEFAULT_MODEL == "tts_models/en/ljspeech/tacotron2-DDC"
    # No explicit model_name -> uses DEFAULT_MODEL (env may override)
    assert "tts_models" in adapter.model_name


# ---------------------------------------------------------------------------
# synthesize() silent-fallback (no coqui installed)
# ---------------------------------------------------------------------------


def test_coqui_synthesize_creates_file(tmp_path: Path) -> None:
    """synthesize() creates a WAV file via silent fallback."""
    out = str(tmp_path / "out.wav")
    with patch("modules.adapters.tts.coqui_tts._COQUI_AVAILABLE", False):
        adapter = CoquiTTSAdapter()
        adapter.synthesize("Hello world", out)
    assert os.path.exists(out)


def test_coqui_synthesize_returns_path(tmp_path: Path) -> None:
    """synthesize() returns the output_path string."""
    out = str(tmp_path / "result.wav")
    with patch("modules.adapters.tts.coqui_tts._COQUI_AVAILABLE", False):
        adapter = CoquiTTSAdapter()
        result = adapter.synthesize("test", out)
    assert result == out


def test_coqui_custom_output_path(tmp_path: Path) -> None:
    """synthesize() respects a custom output_path argument."""
    custom = str(tmp_path / "subdir" / "custom.wav")
    with patch("modules.adapters.tts.coqui_tts._COQUI_AVAILABLE", False):
        adapter = CoquiTTSAdapter()
        result = adapter.synthesize("hello", custom)
    assert result == custom
    assert os.path.exists(custom)


# ---------------------------------------------------------------------------
# Silent WAV validity
# ---------------------------------------------------------------------------


def test_coqui_silent_wav_is_valid(tmp_path: Path) -> None:
    """_write_silent_wav() produces a valid mono WAV readable by stdlib wave."""
    p = str(tmp_path / "silent.wav")
    adapter = CoquiTTSAdapter()
    adapter._write_silent_wav(p)
    with wave.open(p, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 22050
        assert wf.getnframes() > 0


# ---------------------------------------------------------------------------
# list_models
# ---------------------------------------------------------------------------


def test_coqui_list_models_no_lib() -> None:
    """list_models() returns empty list when coqui-tts not installed."""
    with patch("modules.adapters.tts.coqui_tts._COQUI_AVAILABLE", False):
        adapter = CoquiTTSAdapter()
        assert adapter.list_models() == []


# ---------------------------------------------------------------------------
# Constructor parameters
# ---------------------------------------------------------------------------


def test_coqui_constructor_params() -> None:
    """Constructor stores model_name, language, speaker, gpu correctly."""
    adapter = CoquiTTSAdapter(
        model_name="tts_models/en/ljspeech/tacotron2-DDC",
        language="en",
        speaker="speaker_0",
        gpu=True,
    )
    assert adapter.model_name == "tts_models/en/ljspeech/tacotron2-DDC"
    assert adapter._language == "en"
    assert adapter._speaker == "speaker_0"
    assert adapter._gpu is True


def test_coqui_constructor_defaults() -> None:
    """Default constructor uses DEFAULT_MODEL and gpu=False."""
    adapter = CoquiTTSAdapter()
    assert adapter._gpu is False
    assert adapter._speaker is None


# ---------------------------------------------------------------------------
# speak() TTSAdapter compatibility
# ---------------------------------------------------------------------------


def test_adapter_has_speak_method() -> None:
    """CoquiTTSAdapter inherits speak() from TTSAdapter."""
    assert callable(getattr(CoquiTTSAdapter, "speak", None))


def test_speak_creates_file(tmp_path: Path) -> None:
    """speak() delegates to synthesize() and returns a Path."""
    out = tmp_path / "speech.wav"
    with patch("modules.adapters.tts.coqui_tts._COQUI_AVAILABLE", False):
        adapter = CoquiTTSAdapter()
        result = adapter.speak("Hello world", out)
    assert result.exists()
    assert isinstance(result, Path)
