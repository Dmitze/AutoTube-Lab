"""AudioChain: Chain of Responsibility for audio/music generation.

Default priority chain:
  1. SunoAdapter        — 50 songs/day free tier (best AI quality)
  2. PixabayAudioAdapter — 5000 req/day free tier (library tracks)
  3. SilentAudioFallback — stdlib wave, never fails (silent placeholder)

Algorithm: O(k) where k = number of adapters tried (worst case = chain length)
"""
from __future__ import annotations

import logging
import os
import struct
import wave
from pathlib import Path

from modules.adapters.audio.base import AudioAdapter, QuotaExceededError

logger = logging.getLogger(__name__)


class SilentAudioFallback(AudioAdapter):
    """Generates a minimal silent WAV file using stdlib wave — never raises.

    Used as the last link in the AudioChain so that the pipeline always
    gets a valid audio file even when all real services are unavailable.

    Complexity: O(duration_seconds) to write PCM samples

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> fb = SilentAudioFallback()
    >>> fb.is_available()
    True
    >>> with tempfile.TemporaryDirectory() as d:
    ...     p = fb.generate("anything", Path(d) / "silent.wav")
    ...     p.exists()
    True
    """

    def generate(
        self,
        prompt: str,
        output_path: Path,
        duration_seconds: int = 60,
    ) -> Path:
        """Write a silent WAV file to output_path.

        Parameters
        ----------
        prompt:
            Ignored — only present to satisfy the interface.
        output_path:
            Destination file path. Extension is set to .wav automatically
            when the caller passes a .mp3 path (WAV is a valid audio format
            accepted by most video editors and YouTube's upload pipeline).
        duration_seconds:
            Length of the generated silent audio in seconds.

        Returns
        -------
        Path
            Path to the written WAV file (may differ from output_path if
            extension was changed to .wav).

        Complexity: O(duration_seconds × sample_rate)

        Examples
        --------
        >>> from pathlib import Path
        >>> import tempfile
        >>> fb = SilentAudioFallback()
        >>> with tempfile.TemporaryDirectory() as d:
        ...     p = fb.generate("test", Path(d) / "out.mp3")
        ...     p.stat().st_size > 0
        True
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wav_path = output_path.with_suffix(".wav")

        sample_rate = 44100
        n_channels = 1
        sampwidth = 2  # 16-bit PCM
        n_frames = sample_rate * max(1, duration_seconds)
        silent_data = struct.pack("<" + "h" * n_frames, *([0] * n_frames))

        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(sample_rate)
            wf.writeframes(silent_data)

        logger.debug("SilentAudioFallback: wrote %ds silent WAV → %s", duration_seconds, wav_path)
        return wav_path

    def is_available(self) -> bool:
        """Always returns True — stdlib wave is always present.

        Complexity: O(1)

        Examples
        --------
        >>> SilentAudioFallback().is_available()
        True
        """
        return True

    @property
    def service_name(self) -> str:
        """Human-readable service name.

        Examples
        --------
        >>> SilentAudioFallback().service_name
        'Silent Fallback'
        """
        return "Silent Fallback"


class AudioChain:
    """Chain of Responsibility for audio generation with automatic fallback.

    Tries adapters in priority order. Skips an adapter when:
    - adapter.is_available() returns False, or
    - adapter.generate() raises QuotaExceededError.

    Always appends SilentAudioFallback as the last resort so that the
    chain never raises in the absence of real API keys.

    Parameters
    ----------
    adapters:
        Ordered list of AudioAdapter instances. When None, the default
        chain is built from environment variables via from_env().

    Complexity: O(k) per call where k = number of adapters tried

    Examples
    --------
    >>> from pathlib import Path
    >>> from modules.adapters.audio.suno import SunoAdapter
    >>> from modules.adapters.audio.pixabay_audio import PixabayAudioAdapter
    >>> chain = AudioChain([SunoAdapter(api_key=""), PixabayAudioAdapter(api_key="")])
    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as d:
    ...     p = chain.generate("peaceful music", Path(d) / "music.mp3")
    ...     p.exists()
    True
    """

    def __init__(self, adapters: list[AudioAdapter] | None = None) -> None:
        if adapters is None:
            self._adapters: list[AudioAdapter] = _build_default_chain()
        else:
            self._adapters = list(adapters)
        # Always guarantee a fallback at the end
        if not any(isinstance(a, SilentAudioFallback) for a in self._adapters):
            self._adapters.append(SilentAudioFallback())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        output_path: Path,
        duration_seconds: int = 60,
    ) -> Path:
        """Generate music, automatically falling back through the chain.

        Iterates adapters in priority order:
        - Skips adapters where is_available() is False.
        - On QuotaExceededError, logs and moves to the next adapter.
        - On any other exception, logs and moves to the next adapter.
        - SilentAudioFallback at the end of the chain guarantees success.

        Parameters
        ----------
        prompt:
            Text description of the desired music style.
        output_path:
            Destination file path for the generated audio.
        duration_seconds:
            Requested audio duration in seconds.

        Returns
        -------
        Path
            Path to the generated audio file.

        Raises
        ------
        RuntimeError
            Only if SilentAudioFallback itself fails (extremely unlikely).

        Complexity: O(k) worst case, O(1) typical when first adapter succeeds

        Examples
        --------
        >>> from pathlib import Path
        >>> chain = AudioChain([])
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as d:
        ...     p = chain.generate("calm piano", Path(d) / "out.mp3")
        ...     p.exists()
        True
        """
        errors: list[str] = []
        for adapter in self._adapters:
            if not adapter.is_available():
                logger.debug("AudioChain: %s unavailable, skipping", adapter.service_name)
                errors.append(f"{adapter.service_name}: not available")
                continue
            try:
                result = adapter.generate(prompt, output_path, duration_seconds)
                logger.info("AudioChain: used %s for prompt '%s'", adapter.service_name, prompt[:40])
                return result
            except QuotaExceededError as exc:
                logger.warning("AudioChain: %s quota exceeded — %s", adapter.service_name, exc)
                errors.append(f"{adapter.service_name}: quota exceeded")
            except Exception as exc:  # noqa: BLE001
                logger.warning("AudioChain: %s failed — %s", adapter.service_name, exc)
                errors.append(f"{adapter.service_name}: {exc}")

        raise RuntimeError(
            f"AudioChain: all {len(self._adapters)} adapters failed.\n"
            + "\n".join(f"  • {e}" for e in errors)
        )

    def add_adapter(self, adapter: AudioAdapter, priority: int = -1) -> None:
        """Insert an adapter into the chain at the given position.

        Parameters
        ----------
        adapter:
            The adapter instance to add.
        priority:
            Index at which to insert. -1 (default) inserts before the
            SilentAudioFallback tail, keeping it last.

        Complexity: O(k) for list insertion

        Examples
        --------
        >>> from modules.adapters.audio.suno import SunoAdapter
        >>> chain = AudioChain([])
        >>> chain.add_adapter(SunoAdapter(api_key="sk-test"), priority=0)
        >>> chain.adapters[0].service_name
        'Suno AI'
        """
        if priority == -1:
            # Insert before the SilentAudioFallback (always last)
            fallback_idx = next(
                (i for i, a in enumerate(self._adapters) if isinstance(a, SilentAudioFallback)),
                len(self._adapters),
            )
            self._adapters.insert(fallback_idx, adapter)
        else:
            self._adapters.insert(priority, adapter)

    @property
    def adapters(self) -> list[AudioAdapter]:
        """Ordered list of adapters in the chain (read-only view).

        Complexity: O(1)

        Examples
        --------
        >>> chain = AudioChain([])
        >>> len(chain.adapters) >= 1  # at least SilentAudioFallback
        True
        """
        return list(self._adapters)

    @classmethod
    def from_env(cls) -> AudioChain:
        """Build the default chain from environment variables.

        Includes SunoAdapter when SUNO_API_KEY is set, PixabayAudioAdapter
        when PIXABAY_API_KEY is set, and always appends SilentAudioFallback.

        Returns
        -------
        AudioChain
            Configured chain ready for use.

        Complexity: O(1)

        Examples
        --------
        >>> chain = AudioChain.from_env()
        >>> len(chain.adapters) >= 1  # always has SilentAudioFallback
        True
        """
        return cls(adapters=_build_default_chain())


# ---------------------------------------------------------------------------
# Internal chain factory
# ---------------------------------------------------------------------------


def _build_default_chain() -> list[AudioAdapter]:
    """Build the ordered adapter list from environment variables.

    Complexity: O(1)
    """
    chain: list[AudioAdapter] = []

    if os.environ.get("SUNO_API_KEY", "").strip():
        from modules.adapters.audio.suno import SunoAdapter
        chain.append(SunoAdapter())
        logger.debug("AudioChain: SunoAdapter added")

    if os.environ.get("PIXABAY_API_KEY", "").strip():
        from modules.adapters.audio.pixabay_audio import PixabayAudioAdapter
        chain.append(PixabayAudioAdapter())
        logger.debug("AudioChain: PixabayAudioAdapter added")

    chain.append(SilentAudioFallback())
    logger.debug("AudioChain: SilentAudioFallback added (always present)")
    return chain
