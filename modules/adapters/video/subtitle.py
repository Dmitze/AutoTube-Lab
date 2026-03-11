"""Phase 4 — SubtitleGenerator: generates SRT subtitle files from Script.

Roadmap tasks: T-206 through T-210 (EPIC 4.3 Subtitles)
Depends on:   Script dataclass

SRT format:
  1
  00:00:00,000 --> 00:00:03,500
  Привіт, сьогодні ми поговоримо про Python

Algorithm
---------
1. _split_phrases(text, max_chars=42):
     Split at sentence boundaries (. ! ? \n), then word-wrap to ≤ max_chars.
     O(n) where n = len(text).

2. _estimate_timing(phrases, chars_per_second=14):
     duration_i = len(phrase_i) / chars_per_second
     start_i = Σ(duration_j for j < i)
     O(n) sequential accumulation.

3. _format_srt(phrases, timings) → str:
     Build numbered SRT blocks.
     O(n).

Total: O(n) where n = total characters in script.

Chars per second reference:
  Ukrainian TTS (uk-UA-OstapNeural): ~13–15 cps
  English TTS: ~14–16 cps
  Conservative default: 14 cps (slightly slow for readability)
"""
from __future__ import annotations

import re
from pathlib import Path

from ytaimbot_ml.schemas import Script

# Default speech rate: characters per second
_DEFAULT_CPS = 14.0

# Maximum characters per subtitle line (readability limit)
_MAX_LINE_CHARS = 42

# Sentence boundary pattern
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?\n])\s+")


def _format_timestamp(seconds: float) -> str:
    """Convert float seconds to SRT timestamp HH:MM:SS,mmm. O(1).

    Parameters
    ----------
    seconds:
        Time in seconds (non-negative).

    Returns
    -------
    str
        SRT timestamp string.

    Examples
    --------
    >>> _format_timestamp(65.5)
    '00:01:05,500'
    >>> _format_timestamp(0.0)
    '00:00:00,000'
    """
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class SubtitleGenerator:
    """Generates SRT subtitle files from a Script dataclass.

    Parameters
    ----------
    chars_per_second:
        Estimated speech rate for timing. Default 14 cps.
    max_line_chars:
        Max characters per subtitle line. Default 42.

    Complexity
    ----------
    generate_srt(): O(n) where n = total characters in script

    Examples
    --------
    >>> gen = SubtitleGenerator()
    >>> gen.chars_per_second
    14.0
    """

    def __init__(
        self,
        chars_per_second: float = _DEFAULT_CPS,
        max_line_chars: int = _MAX_LINE_CHARS,
    ) -> None:
        self.chars_per_second = chars_per_second
        self.max_line_chars = max_line_chars

    def generate_srt(self, script: Script, output_path: Path) -> Path:
        """Generate SRT subtitle file from a Script.

        Parameters
        ----------
        script:
            Script with sections and text content.
        output_path:
            Destination .srt file path.

        Returns
        -------
        Path
            Path to the written SRT file.

        Complexity
        ----------
        O(n) where n = total characters in script.full_text

        Examples
        --------
        >>> from pathlib import Path
        >>> from ytaimbot_ml.schemas import Script, ScriptSection
        >>> s = Script(plan_id="t1", sections=[ScriptSection("hook", "Hello world.")])
        >>> gen = SubtitleGenerator()
        >>> path = gen.generate_srt(s, Path("/tmp/test.srt"))  # doctest: +SKIP
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        full_text = script.full_text
        phrases = self._split_phrases(full_text)
        timings = self._estimate_timing(phrases)
        srt_content = self._format_srt(phrases, timings)

        output_path.write_text(srt_content, encoding="utf-8")
        return output_path

    def generate_srt_string(self, script: Script) -> str:
        """Generate SRT content as a string (no file I/O).

        Parameters
        ----------
        script:
            Script dataclass.

        Returns
        -------
        str
            SRT-formatted subtitle content.

        Complexity
        ----------
        O(n)

        Examples
        --------
        >>> from ytaimbot_ml.schemas import Script, ScriptSection
        >>> s = Script(plan_id="t1", sections=[ScriptSection("hook", "Hi.")])
        >>> gen = SubtitleGenerator()
        >>> srt = gen.generate_srt_string(s)
        >>> srt.startswith("1")
        True
        """
        full_text = script.full_text
        phrases = self._split_phrases(full_text)
        timings = self._estimate_timing(phrases)
        return self._format_srt(phrases, timings)

    def _split_phrases(self, text: str) -> list[str]:
        """Split text into subtitle phrases ≤ max_line_chars. O(n).

        Split first at sentence boundaries, then word-wrap long sentences.

        Parameters
        ----------
        text:
            Full script text.

        Returns
        -------
        list[str]
            List of subtitle phrases.

        Examples
        --------
        >>> gen = SubtitleGenerator(max_line_chars=20)
        >>> phrases = gen._split_phrases("Hello world. This is a test.")
        >>> all(len(p) <= 20 for p in phrases)
        True
        """
        if not text.strip():
            return []

        sentences = _SENTENCE_BOUNDARY.split(text.strip())
        phrases: list[str] = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) <= self.max_line_chars:
                phrases.append(sentence)
                continue
            # Word-wrap long sentences
            words = sentence.split()
            current = ""
            for word in words:
                if len(current) + len(word) + 1 <= self.max_line_chars:
                    current = f"{current} {word}".strip()
                else:
                    if current:
                        phrases.append(current)
                    current = word
            if current:
                phrases.append(current)

        return phrases

    def _estimate_timing(
        self, phrases: list[str]
    ) -> list[tuple[float, float]]:
        """Estimate start/end timestamps for each phrase. O(n).

        Parameters
        ----------
        phrases:
            List of subtitle phrases.

        Returns
        -------
        list[tuple[float, float]]
            List of (start_seconds, end_seconds) per phrase.

        Examples
        --------
        >>> gen = SubtitleGenerator(chars_per_second=10.0)
        >>> timings = gen._estimate_timing(["Hello"])
        >>> timings[0][0]
        0.0
        >>> timings[0][1]
        0.5
        """
        timings: list[tuple[float, float]] = []
        cursor = 0.0
        for phrase in phrases:
            duration = max(0.5, len(phrase) / self.chars_per_second)
            timings.append((cursor, cursor + duration))
            cursor += duration + 0.1  # 100ms gap between subtitles
        return timings

    @staticmethod
    def _format_srt(
        phrases: list[str], timings: list[tuple[float, float]]
    ) -> str:
        """Format phrases and timings as SRT content. O(n).

        Parameters
        ----------
        phrases:
            List of subtitle phrases.
        timings:
            Corresponding (start, end) tuples.

        Returns
        -------
        str
            SRT-formatted string.

        Examples
        --------
        >>> srt = SubtitleGenerator._format_srt(["Hi"], [(0.0, 1.0)])
        >>> "00:00:00,000 --> 00:00:01,000" in srt
        True
        """
        blocks: list[str] = []
        for i, (phrase, (start, end)) in enumerate(zip(phrases, timings), start=1):
            blocks.append(
                f"{i}\n"
                f"{_format_timestamp(start)} --> {_format_timestamp(end)}\n"
                f"{phrase}\n"
            )
        return "\n".join(blocks)

