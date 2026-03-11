"""Abstract base for audio/music generation adapters.

All implementations must:
- Accept a text prompt describing the music style
- Write a valid audio file to output_path
- Return the output_path on success
- Raise QuotaExceededError when daily limit is reached
- Never make real network calls in tests

Complexity: O(1) interface definition
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class QuotaExceededError(Exception):
    """Raised when the adapter's daily/monthly quota is exhausted."""


class AudioAdapter(ABC):
    """Abstract interface for music/audio generation.

    All implementations must:
    - Accept a text prompt describing the music style
    - Write a valid audio file to output_path
    - Return the output_path on success
    - Raise QuotaExceededError when daily limit is reached
    - Never make real network calls in tests

    Complexity: O(1) interface

    Examples
    --------
    >>> adapter = SunoAdapter(api_key="")
    >>> adapter.is_available()
    False
    >>> adapter.service_name
    'Suno AI'
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        output_path: Path,
        duration_seconds: int = 60,
    ) -> Path:
        """Generate music from a text prompt and save to output_path.

        Parameters
        ----------
        prompt:
            Text description of the desired music style.
        output_path:
            Destination file path for the generated audio.
        duration_seconds:
            Requested duration of the generated audio in seconds.

        Returns
        -------
        Path
            Path to the generated audio file.

        Raises
        ------
        QuotaExceededError
            When the adapter's daily/monthly quota is exhausted.

        Complexity: O(1) abstract definition
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this adapter has quota remaining and is configured.

        Complexity: O(1)

        Examples
        --------
        >>> adapter = SunoAdapter(api_key="")
        >>> adapter.is_available()
        False
        """

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Human-readable service name for logging.

        Examples
        --------
        >>> adapter = SunoAdapter(api_key="")
        >>> adapter.service_name
        'Suno AI'
        """
