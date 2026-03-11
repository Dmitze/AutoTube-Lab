"""Phase 2 — EdgeTTSAdapter: Microsoft Edge Neural TTS (primary TTS).

Roadmap tasks: T-098 through T-108 (EPIC 2.2)
Depends on:   edge-tts (async), pydub, TTSAdapter ABC

Configuration:
  TTS_VOICE    : voice name (default: uk-UA-OstapNeural)
  TTS_LANGUAGE : language code (default: uk)
  TTS_GENDER   : "male" | "female" (default: male)

Supported voices:
  Ukrainian : uk-UA-OstapNeural (M), uk-UA-PolinaNeural (F)
  English   : en-US-GuyNeural (M), en-US-JennyNeural (F)
  Russian   : ru-RU-DmitryNeural (M), ru-RU-SvetlanaNeural (F)

Algorithm
---------
speak() pipeline:
  1. _split_text(text, max_chars=3000) → list[str]  O(n)
     Split at sentence boundary (. ! ? \n) to avoid mid-sentence cut
  2. For each chunk: edge_tts.Communicate(chunk, voice).save(tmp.mp3)
     → async, run via asyncio.run()
  3. Concatenate chunks with pydub AudioSegment            O(n_chunks)
  4. Export to output_path as MP3                          O(samples)

  Total: O(n) where n = len(text)
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import tempfile
from pathlib import Path

from modules.adapters.base import TTSAdapter

logger = logging.getLogger(__name__)

# Voice selection table: language → gender → voice name
VOICE_MAP: dict[str, dict[str, str]] = {
    "uk": {
        "male":   "uk-UA-OstapNeural",
        "female": "uk-UA-PolinaNeural",
    },
    "en": {
        "male":   "en-US-GuyNeural",
        "female": "en-US-JennyNeural",
    },
    "ru": {
        "male":   "ru-RU-DmitryNeural",
        "female": "ru-RU-SvetlanaNeural",
    },
    "de": {
        "male":   "de-DE-ConradNeural",
        "female": "de-DE-KatjaNeural",
    },
    "pl": {
        "male":   "pl-PL-MarekNeural",
        "female": "pl-PL-ZofiaNeural",
    },
}

_MAX_CHUNK_CHARS = 3000
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?\n])\s+")


def select_voice(lang: str = "uk", gender: str = "male") -> str:
    """Return the Edge TTS voice name for the given language and gender.

    Algorithm: O(1) hash map lookup.

    Parameters
    ----------
    lang:
        ISO 639-1 language code (default "uk").
    gender:
        "male" or "female" (default "male").

    Returns
    -------
    str
        Voice name string for edge-tts.

    Examples
    --------
    >>> select_voice("uk", "male")
    'uk-UA-OstapNeural'
    >>> select_voice("xx", "male")  # unknown → fallback to English
    'en-US-GuyNeural'
    """
    voices = VOICE_MAP.get(lang, VOICE_MAP["en"])
    return voices.get(gender, voices["male"])


class EdgeTTSAdapter(TTSAdapter):
    """Microsoft Edge Neural TTS adapter.

    Parameters
    ----------
    voice:
        Voice name. Falls back to TTS_VOICE env var, then uk-UA-OstapNeural.
    language:
        ISO 639-1 code. Falls back to TTS_LANGUAGE env var, then "uk".
    gender:
        "male" or "female". Falls back to TTS_GENDER env var.

    Complexity
    ----------
    speak(): O(n) where n = len(text)

    Examples
    --------
    >>> adapter = EdgeTTSAdapter(voice="uk-UA-OstapNeural")
    >>> adapter.voice
    'uk-UA-OstapNeural'
    """

    def __init__(
        self,
        voice: str | None = None,
        language: str | None = None,
        gender: str = "male",
    ) -> None:
        lang = language or os.environ.get("TTS_LANGUAGE", "uk")
        default_voice = select_voice(lang, gender)
        self.voice = voice or os.environ.get("TTS_VOICE", default_voice)
        self.language = lang

    def speak(self, text: str, output_path: Path) -> Path:
        """Synthesize speech and save to output_path (MP3).

        Parameters
        ----------
        text:
            Input text (any length — automatically chunked if > 3000 chars).
        output_path:
            Destination MP3 file path.

        Returns
        -------
        Path
            Path to the generated MP3 file.

        Raises
        ------
        RuntimeError
            If edge-tts is not installed or synthesis fails.

        Complexity
        ----------
        O(n) where n = len(text)

        Examples
        --------
        >>> from pathlib import Path
        >>> adapter = EdgeTTSAdapter()
        >>> path = adapter.speak("Привіт!", Path("/tmp/test.mp3"))  # doctest: +SKIP
        """
        try:
            import edge_tts  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "edge-tts not installed: pip install edge-tts"
            ) from exc

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        chunks = self._split_text(text)
        logger.debug(
            "EdgeTTS: synthesizing %d chars in %d chunk(s) with voice=%s",
            len(text),
            len(chunks),
            self.voice,
        )

        if len(chunks) == 1:
            asyncio.run(self._synthesize_chunk(chunks[0], output_path, edge_tts))
        else:
            output_path = self._synthesize_and_merge(chunks, output_path, edge_tts)

        logger.info("EdgeTTS: saved audio → %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _split_text(self, text: str, max_chars: int = _MAX_CHUNK_CHARS) -> list[str]:
        """Split text at sentence boundaries. O(n).

        Parameters
        ----------
        text:
            Input text string.
        max_chars:
            Maximum characters per chunk.

        Returns
        -------
        list[str]
            List of text chunks, each ≤ max_chars characters.

        Examples
        --------
        >>> a = EdgeTTSAdapter()
        >>> chunks = a._split_text("Hello. World.", max_chars=7)
        >>> all(len(c) <= 7 for c in chunks)
        True
        """
        if len(text) <= max_chars:
            return [text]

        sentences = _SENTENCE_BOUNDARY.split(text)
        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= max_chars:
                current = f"{current} {sentence}".strip()
            else:
                if current:
                    chunks.append(current)
                # If single sentence exceeds max_chars, hard-split it
                if len(sentence) > max_chars:
                    for i in range(0, len(sentence), max_chars):
                        chunks.append(sentence[i : i + max_chars])
                    current = ""
                else:
                    current = sentence

        if current:
            chunks.append(current)

        return chunks or [text]

    async def _synthesize_chunk(
        self, text: str, output_path: Path, edge_tts_module
    ) -> None:
        """Async synthesis of a single chunk. Called via asyncio.run()."""
        communicate = edge_tts_module.Communicate(text, self.voice)
        await communicate.save(str(output_path))

    def _synthesize_and_merge(
        self, chunks: list[str], output_path: Path, edge_tts_module
    ) -> Path:
        """Synthesize multiple chunks and merge into one MP3 file. O(n_chunks).

        Uses pydub for concatenation if available; falls back to binary concat.
        """
        tmp_files: list[Path] = []
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp = Path(tmpdir)
                for i, chunk in enumerate(chunks):
                    chunk_path = tmp / f"chunk_{i:04d}.mp3"
                    asyncio.run(
                        self._synthesize_chunk(chunk, chunk_path, edge_tts_module)
                    )
                    tmp_files.append(chunk_path)

                self._merge_mp3(tmp_files, output_path)
        except Exception as exc:
            logger.error("EdgeTTS merge failed: %s", exc)
            raise
        return output_path

    @staticmethod
    def _merge_mp3(files: list[Path], output: Path) -> None:
        """Concatenate MP3 files using pydub or binary fallback. O(n_files).

        Prefers pydub for proper audio concatenation; falls back to
        binary file concatenation if pydub is unavailable.
        """
        try:
            from pydub import AudioSegment  # noqa: PLC0415

            combined = AudioSegment.empty()
            for f in files:
                combined += AudioSegment.from_mp3(str(f))
            combined.export(str(output), format="mp3")
            logger.debug("EdgeTTS: merged %d chunks via pydub", len(files))
        except ImportError:
            logger.warning("pydub not installed — using binary MP3 concat")
            with open(output, "wb") as out:
                for f in files:
                    out.write(f.read_bytes())

