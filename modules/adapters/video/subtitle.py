"""Phase 3 — SubtitleGenerator: generates SRT/ASS subtitles for videos.

Roadmap tasks: T-356 through T-370 (EPIC 3.5 Subtitles)
Depends on:   Script (sections with text), audio duration

SRT format:
  1
  00:00:00,000 --> 00:00:03,500
  Привіт, сьогодні ми поговоримо про...

Algorithm
---------
Timing alignment:
  1. Split script text into phrases (≤ 42 chars, sentence boundary) → O(n)
  2. Estimate duration per phrase:
       duration = len(phrase) / chars_per_second  (default 14 cps)
  3. Accumulate timestamps → O(n)
  4. Write SRT file        → O(n)

  Chars per second (Ukrainian TTS): ~12–16 cps
  Max line length for readability: 42 characters

Status: 🔲 Pending — T-356 (Phase 3)
"""
from __future__ import annotations

from pathlib import Path

# TODO: T-356 — implement SubtitleGenerator class
# TODO: T-357 — implement generate_srt(script, audio_path) → Path
# TODO: T-358 — implement _split_phrases(text, max_chars=42) → list[str]
# TODO: T-359 — implement _estimate_timing(phrases) → list[tuple[float,float]]


class SubtitleGenerator:
    """TODO: implement in T-356."""

    def generate_srt(self, script, audio_path: Path) -> Path:  # type: ignore[override]
        """TODO: T-357. Returns path to .srt file."""
        raise NotImplementedError("T-356 pending")
