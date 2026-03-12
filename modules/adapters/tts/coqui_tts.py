"""Phase 2 -- CoquiTTSAdapter: offline Coqui TTS with graceful fallback.

Roadmap tasks: T-116 through T-120 (T-395, EPIC 3.3)
Depends on:   TTS (optional), TTSAdapter ABC

Configuration:
  COQUI_MODEL_NAME : model identifier
                     (default: tts_models/en/ljspeech/tacotron2-DDC)

Graceful degradation: if coqui-tts is not installed, synthesize() writes a
minimal silent WAV file and logs a warning rather than raising.

Algorithm
---------
speak() pipeline:
  1. Load TTS model (cached after first load)       -> O(1) after init
  2. tts.tts_to_file(text, file_path=output_path)   -> O(tokens)
  3. Return output_path

  Synthesis: O(n) where n = text length in tokens

Status: Implemented -- T-395 (Phase 3)
"""
from __future__ import annotations

import logging
import os
import wave
from pathlib import Path

log = logging.getLogger(__name__)

try:
    from TTS.api import TTS as CoquiLib  # type: ignore[import]
    _COQUI_AVAILABLE = True
except ImportError:
    _COQUI_AVAILABLE = False
    log.debug("coqui-tts not installed; CoquiTTSAdapter will use silent WAV fallback")

from modules.adapters.tts.base import TTSAdapter


class CoquiTTSAdapter(TTSAdapter):
    """Local TTS using Coqui TTS models. No API key required.

    If coqui-tts is not installed, synthesize() creates a minimal valid
    WAV file (silence) and logs a warning instead of raising.

    Algorithm: O(n) synthesis where n = text length in tokens.

    Parameters
    ----------
    model_name : str
        Coqui model identifier. Reads COQUI_MODEL_NAME env var when not
        provided, falling back to DEFAULT_MODEL.
    language : str
        Language code. Default "en".
    speaker : str | None
        Speaker name for multi-speaker models. Default None.
    gpu : bool
        Whether to use GPU for synthesis. Default False.

    Examples
    --------
    >>> adapter = CoquiTTSAdapter()
    >>> adapter.is_available
    False
    """

    DEFAULT_MODEL = "tts_models/en/ljspeech/tacotron2-DDC"

    _WAV_CHANNELS = 1
    _WAV_SAMPWIDTH = 2
    _WAV_FRAMERATE = 22050
    _WAV_SILENCE_FRAMES = 22050

    def __init__(
        self,
        model_name: str = "",
        language: str = "en",
        speaker: str | None = None,
        gpu: bool = False,
    ) -> None:
        """Initialise the adapter with lazy model loading.

        Parameters
        ----------
        model_name : str
            Coqui model identifier. Reads COQUI_MODEL_NAME env var when
            empty; defaults to DEFAULT_MODEL.
        language : str
            Language code. Default "en".
        speaker : str | None
            Speaker for multi-speaker models. Default None.
        gpu : bool
            Use GPU acceleration. Default False.

        Complexity: O(1).

        Examples
        --------
        >>> a = CoquiTTSAdapter(model_name="tts_models/en/ljspeech/tacotron2-DDC")
        >>> a.model_name
        'tts_models/en/ljspeech/tacotron2-DDC'
        """
        resolved = model_name or os.environ.get("COQUI_MODEL_NAME", self.DEFAULT_MODEL)
        self.model_name: str = resolved
        self._language = language
        self._speaker = speaker
        self._gpu = gpu
        self._tts = None

        log.debug(
            "CoquiTTSAdapter initialised (model=%s, language=%s, gpu=%s)",
            self.model_name,
            language,
            gpu,
        )

    @property
    def is_available(self) -> bool:
        """True if the coqui-tts library is installed. O(1).

        Examples
        --------
        >>> CoquiTTSAdapter().is_available
        False
        """
        return _COQUI_AVAILABLE

    def synthesize(self, text: str, output_path: str = "/tmp/coqui_out.wav") -> str:
        """Synthesize text to a WAV file at output_path. O(n).

        Falls back to silent WAV if coqui-tts is not installed.

        Parameters
        ----------
        text : str
            Input text to synthesize.
        output_path : str
            Destination WAV file path. Parent directory is created if needed.

        Returns
        -------
        str
            The resolved output_path.

        Examples
        --------
        >>> import tempfile, os
        >>> adapter = CoquiTTSAdapter()
        >>> p = os.path.join(tempfile.gettempdir(), "coqui_test.wav")
        >>> adapter.synthesize("hello", p) == p
        True
        """
        parent = os.path.dirname(os.path.abspath(output_path))
        if parent:
            os.makedirs(parent, exist_ok=True)

        if not _COQUI_AVAILABLE:
            log.warning(
                "coqui-tts not installed -- writing silent WAV to %s", output_path
            )
            self._write_silent_wav(output_path)
            return output_path

        if self._tts is None:
            log.info("CoquiTTSAdapter: loading model %s ...", self.model_name)
            self._tts = CoquiLib(self.model_name, gpu=self._gpu)

        kwargs: dict = {"text": text, "file_path": output_path}
        if self._speaker is not None:
            kwargs["speaker"] = self._speaker
        if self._language:
            kwargs["language"] = self._language

        self._tts.tts_to_file(**kwargs)
        log.info("CoquiTTSAdapter: synthesized %d chars -> %s", len(text), output_path)
        return output_path

    def speak(self, text: str, output_path: Path) -> Path:
        """TTSAdapter ABC implementation -- delegates to synthesize(). O(n).

        Parameters
        ----------
        text : str
            Input text.
        output_path : Path
            Destination WAV file path.

        Returns
        -------
        Path
            Path to the generated WAV file.

        Examples
        --------
        >>> import tempfile
        >>> from pathlib import Path
        >>> adapter = CoquiTTSAdapter()
        >>> p = Path(tempfile.mktemp(suffix=".wav"))
        >>> result = adapter.speak("hi", p)
        >>> result.exists()
        True
        """
        out = self.synthesize(text, str(output_path))
        return Path(out)

    def list_models(self) -> list[str]:
        """List available Coqui TTS model names. O(1).

        Returns empty list if coqui-tts is not installed.

        Returns
        -------
        list[str]
            Available model identifiers.

        Examples
        --------
        >>> CoquiTTSAdapter().list_models()
        []
        """
        if not _COQUI_AVAILABLE:
            return []
        try:
            return CoquiLib.list_models()
        except Exception as exc:
            log.debug("CoquiTTSAdapter.list_models() failed: %s", exc)
            return []

    def _write_silent_wav(self, path: str) -> None:
        """Write a minimal silent WAV file using stdlib wave module. O(1).

        Produces a mono 16-bit 22050 Hz WAV containing 1 second of silence.

        Parameters
        ----------
        path : str
            Destination file path (parent directory must already exist).

        Examples
        --------
        >>> import tempfile, wave, os
        >>> adapter = CoquiTTSAdapter()
        >>> p = os.path.join(tempfile.gettempdir(), "silent.wav")
        >>> adapter._write_silent_wav(p)
        >>> wave.open(p).getnchannels()
        1
        """
        silence = b"\x00" * self._WAV_SAMPWIDTH * self._WAV_SILENCE_FRAMES
        with wave.open(path, "wb") as wf:
            wf.setnchannels(self._WAV_CHANNELS)
            wf.setsampwidth(self._WAV_SAMPWIDTH)
            wf.setframerate(self._WAV_FRAMERATE)
            wf.writeframes(silence)
        log.debug(
            "CoquiTTSAdapter: wrote %d-byte silent WAV to %s", len(silence), path
        )
