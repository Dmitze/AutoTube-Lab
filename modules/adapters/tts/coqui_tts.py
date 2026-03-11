"""Phase 2 — CoquiTTSAdapter: offline Coqui TTS (fallback).

Roadmap tasks: T-116 through T-120 (EPIC 2.2 fallback)
Depends on:   TTS (Coqui) library, TTSAdapter ABC

Configuration:
  COQUI_MODEL_PATH : path to downloaded model (default: ./data/tts_models/)
  COQUI_MODEL_NAME : model identifier (default: tts_models/uk/mai/glow-tts)

Use when: Edge TTS unavailable (no internet on VPS, rate limited)

Algorithm
---------
speak() pipeline:
  1. Load TTS model (cached after first load)       → O(1) after init
  2. tts.tts_to_file(text, file_path=output_path)   → O(tokens)
  3. Return output_path

  Model loading: O(model_size) at startup, O(1) after cache

Status: 🔲 Pending — T-116 (Phase 2)
"""
from __future__ import annotations

from pathlib import Path

# TODO: T-116 — implement CoquiTTSAdapter(TTSAdapter)
# TODO: T-117 — implement speak(text, output_path) → Path
# TODO: T-118 — implement lazy model loading (load on first call)

from modules.adapters.tts.base import TTSAdapter


class CoquiTTSAdapter(TTSAdapter):
    """TODO: implement in T-116."""

    def __init__(self, model_name: str = "tts_models/uk/mai/glow-tts") -> None:
        self.model_name = model_name
        self._tts = None  # lazy load

    def speak(self, text: str, output_path: Path) -> Path:
        """TODO: T-117."""
        raise NotImplementedError("T-116 pending")
