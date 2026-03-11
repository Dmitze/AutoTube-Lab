"""Audio adapter package for YTAIMBot.

Provides AI music generation via a Chain-of-Responsibility pattern:
  SunoAdapter → PixabayAudioAdapter → SilentAudioFallback

Usage
-----
>>> from modules.adapters.audio import AudioChain
>>> chain = AudioChain.from_env()
>>> # path = chain.generate("cozy Ghibli ambient piano", Path("/tmp/music.mp3"))
"""
from __future__ import annotations

from modules.adapters.audio.audio_chain import AudioChain, SilentAudioFallback
from modules.adapters.audio.base import AudioAdapter, QuotaExceededError
from modules.adapters.audio.pixabay_audio import PixabayAudioAdapter
from modules.adapters.audio.suno import SunoAdapter

__all__ = [
    "AudioAdapter",
    "QuotaExceededError",
    "SunoAdapter",
    "PixabayAudioAdapter",
    "AudioChain",
    "SilentAudioFallback",
]
