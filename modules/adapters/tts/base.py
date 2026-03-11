"""Phase 2 — TTSAdapter ABC: interface for all TTS adapters.

Status: 🔲 Pending — T-101 (Phase 2)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TTSAdapter(ABC):
    """Abstract base class for Text-to-Speech adapters.

    All implementations MUST:
    - Accept text string, return Path to WAV file
    - Output format: WAV 22050Hz mono
    - Support async generation for long texts (chunking)

    Complexity: speak() → O(len(text)) I/O
    """

    @abstractmethod
    def speak(self, text: str, output_path: Path) -> Path:
        """Convert text to speech.

        Parameters
        ----------
        text:
            Input text to synthesize.
        output_path:
            Destination WAV file path.

        Returns
        -------
        Path
            Path to generated WAV file.
        """
        ...  # pragma: no cover
