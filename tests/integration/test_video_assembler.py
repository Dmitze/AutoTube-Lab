"""Tests for Phase 4 video pipeline: VideoAssembler, ThumbnailGenerator, SubtitleGenerator.

VideoAssembler tests use mocked moviepy — no real FFmpeg in CI.
ThumbnailGenerator tests use real Pillow (skipped if not installed).
SubtitleGenerator tests are pure Python — no external deps.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ytaimbot_ml.schemas import ContentPlan, Script, ScriptSection, VideoAsset


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_script(plan_id: str = "t1", words_per_section: int = 50) -> Script:
    return Script(
        plan_id=plan_id,
        language="uk",
        sections=[
            ScriptSection(name=name, text=" ".join(["слово"] * words_per_section))
            for name in ["hook", "intro", "body_1", "body_2", "body_3", "cta"]
        ],
    )


def _make_plan() -> ContentPlan:
    return ContentPlan(
        trend_id="python_tutorial",
        title="Python Tutorial",
        outline=["Intro", "Main", "CTA"],
        keywords=["python", "tutorial"],
    )


# ===========================================================================
# SubtitleGenerator tests (pure Python — always run)
# ===========================================================================


class TestSubtitleFormatTimestamp:
    def test_zero(self):
        from modules.adapters.video.subtitle import _format_timestamp
        assert _format_timestamp(0.0) == "00:00:00,000"

    def test_one_hour(self):
        from modules.adapters.video.subtitle import _format_timestamp
        assert _format_timestamp(3600.0) == "01:00:00,000"

    def test_one_minute_30(self):
        from modules.adapters.video.subtitle import _format_timestamp
        assert _format_timestamp(90.5) == "00:01:30,500"

    def test_milliseconds_rounded(self):
        from modules.adapters.video.subtitle import _format_timestamp
        ts = _format_timestamp(1.123)
        assert ts.endswith(",123")

    def test_negative_clamps_to_zero(self):
        from modules.adapters.video.subtitle import _format_timestamp
        assert _format_timestamp(-5.0) == "00:00:00,000"


class TestSubtitleGenerator:
    def _gen(self):
        from modules.adapters.video.subtitle import SubtitleGenerator
        return SubtitleGenerator(chars_per_second=14.0, max_line_chars=42)

    def test_split_short_sentence(self):
        gen = self._gen()
        phrases = gen._split_phrases("Hello world.")
        assert phrases == ["Hello world."]

    def test_split_long_wraps(self):
        gen = self._gen()
        long_text = "This is a very long sentence that should definitely be split into multiple subtitle lines."
        phrases = gen._split_phrases(long_text)
        assert all(len(p) <= 42 for p in phrases)

    def test_split_empty_returns_empty(self):
        gen = self._gen()
        assert gen._split_phrases("") == []

    def test_split_sentence_boundary(self):
        gen = self._gen()
        phrases = gen._split_phrases("First. Second.")
        assert len(phrases) >= 2

    def test_timing_starts_at_zero(self):
        gen = self._gen()
        timings = gen._estimate_timing(["Hello"])
        assert timings[0][0] == 0.0

    def test_timing_end_after_start(self):
        gen = self._gen()
        timings = gen._estimate_timing(["Hello", "World"])
        for start, end in timings:
            assert end > start

    def test_timing_sequential(self):
        gen = self._gen()
        timings = gen._estimate_timing(["A", "B", "C"])
        for i in range(1, len(timings)):
            assert timings[i][0] >= timings[i-1][1]

    def test_format_srt_structure(self):
        from modules.adapters.video.subtitle import SubtitleGenerator
        srt = SubtitleGenerator._format_srt(["Hello"], [(0.0, 1.0)])
        assert "1\n" in srt
        assert "-->" in srt
        assert "Hello" in srt

    def test_format_srt_multiple_blocks(self):
        from modules.adapters.video.subtitle import SubtitleGenerator
        srt = SubtitleGenerator._format_srt(["A", "B", "C"], [(0,1), (1.1,2), (2.1,3)])
        assert "1\n" in srt
        assert "2\n" in srt
        assert "3\n" in srt

    def test_generate_srt_string_from_script(self):
        gen = self._gen()
        script = _make_script()
        srt = gen.generate_srt_string(script)
        assert isinstance(srt, str)
        assert len(srt) > 0
        assert "-->" in srt

    def test_generate_srt_file(self, tmp_path):
        gen = self._gen()
        script = _make_script()
        output = tmp_path / "test.srt"
        result = gen.generate_srt(script, output)
        assert result.exists()
        assert result.suffix == ".srt"
        content = result.read_text(encoding="utf-8")
        assert "-->" in content

    def test_generate_srt_creates_parent_dirs(self, tmp_path):
        gen = self._gen()
        script = _make_script()
        output = tmp_path / "deep" / "dir" / "test.srt"
        gen.generate_srt(script, output)
        assert output.exists()


# ===========================================================================
# ThumbnailGenerator tests (requires Pillow)
# ===========================================================================


class TestThumbnailGenerator:
    def _gen(self, tmp_path):
        try:
            from modules.adapters.video.thumbnail import ThumbnailGenerator
        except ImportError:
            pytest.skip("Pillow not installed")
        return ThumbnailGenerator(output_dir=str(tmp_path), width=320, height=180)

    def test_generate_returns_path(self, tmp_path):
        gen = self._gen(tmp_path)
        plan = _make_plan()
        try:
            result = gen.generate(plan)
            assert isinstance(result, Path)
        except ImportError:
            pytest.skip("Pillow not installed")

    def test_generate_creates_file(self, tmp_path):
        gen = self._gen(tmp_path)
        plan = _make_plan()
        try:
            result = gen.generate(plan)
            assert result.exists()
        except ImportError:
            pytest.skip("Pillow not installed")

    def test_generate_correct_dimensions(self, tmp_path):
        try:
            from PIL import Image
            from modules.adapters.video.thumbnail import ThumbnailGenerator
        except ImportError:
            pytest.skip("Pillow not installed")
        gen = ThumbnailGenerator(output_dir=str(tmp_path), width=320, height=180)
        plan = _make_plan()
        result = gen.generate(plan)
        img = Image.open(str(result))
        assert img.size == (320, 180)

    def test_generate_png_format(self, tmp_path):
        gen = self._gen(tmp_path)
        plan = _make_plan()
        try:
            result = gen.generate(plan)
            assert result.suffix.lower() == ".png"
        except ImportError:
            pytest.skip("Pillow not installed")


# ===========================================================================
# VideoAssembler tests (mocked moviepy)
# ===========================================================================


class TestVideoAssembler:
    def test_missing_audio_raises_file_not_found(self, tmp_path):
        from modules.adapters.video.assembler import VideoAssembler
        assembler = VideoAssembler(output_dir=str(tmp_path))
        script = _make_script()
        with pytest.raises(FileNotFoundError):
            assembler.assemble(script, Path("/nonexistent/audio.mp3"))

    def test_missing_moviepy_raises_import_error(self, tmp_path):
        from modules.adapters.video.assembler import VideoAssembler
        assembler = VideoAssembler(output_dir=str(tmp_path))
        script = _make_script()
        audio_path = tmp_path / "audio.mp3"
        audio_path.write_bytes(b"fake")
        with patch.dict("sys.modules", {"moviepy": None}):
            with pytest.raises((ImportError, Exception)):
                assembler.assemble(script, audio_path)

    def test_video_asset_ready_property(self):
        asset = VideoAsset(
            plan_id="t1",
            video_path="/tmp/video.mp4",
            thumbnail_path="/tmp/thumb.png",
        )
        assert asset.ready is True

    def test_video_asset_not_ready_empty_paths(self):
        asset = VideoAsset(plan_id="t1")
        assert asset.ready is False

    def test_assembler_default_fps(self):
        from modules.adapters.video.assembler import VideoAssembler
        assert VideoAssembler().fps == 30

    def test_assembler_default_crf(self):
        from modules.adapters.video.assembler import VideoAssembler
        assert VideoAssembler().crf == 23

    def test_assembler_default_resolution(self):
        from modules.adapters.video.assembler import VideoAssembler
        assert VideoAssembler().resolution == (1920, 1080)

