"""Unit tests for SunoAdapter and PixabayAudioAdapter.

All tests use no real network calls — no API keys required.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from modules.adapters.audio.audio_chain import SilentAudioFallback
from modules.adapters.audio.base import QuotaExceededError
from modules.adapters.audio.pixabay_audio import PixabayAudioAdapter
from modules.adapters.audio.suno import SunoAdapter


# ===========================================================================
# SunoAdapter — availability & configuration
# ===========================================================================


class TestSunoAvailability:
    def test_suno_no_key_not_available(self):
        assert SunoAdapter(api_key="").is_available() is False

    def test_suno_has_key_available(self):
        assert SunoAdapter(api_key="fake_key").is_available() is True

    def test_suno_service_name(self):
        assert SunoAdapter(api_key="").service_name == "Suno AI"

    def test_suno_max_daily_limit(self):
        assert SunoAdapter.MAX_DAILY_GENERATIONS == 50

    def test_suno_max_poll_attempts(self):
        assert SunoAdapter.MAX_POLL_ATTEMPTS == 30

    def test_suno_quota_exhausted_not_available(self):
        adapter = SunoAdapter(api_key="sk-test", daily_limit=2)
        adapter._generations_today = 2
        assert adapter.is_available() is False


# ===========================================================================
# SunoAdapter — style presets
# ===========================================================================


class TestSunoStylePresets:
    def test_suno_style_presets_ghibli(self):
        prompt = SunoAdapter().get_style_prompt("ghibli_asmr")
        assert "piano" in prompt.lower()

    def test_suno_style_presets_hype(self):
        prompt = SunoAdapter().get_style_prompt("hype_characters")
        assert "anime" in prompt.lower()

    def test_suno_style_presets_unknown(self):
        prompt = SunoAdapter().get_style_prompt("xyz_totally_unknown_niche")
        assert prompt == SunoAdapter.STYLE_PRESETS["generic"]

    def test_suno_all_presets_no_vocals(self):
        for niche, preset in SunoAdapter.STYLE_PRESETS.items():
            assert "no vocals" in preset.lower(), (
                f"Preset '{niche}' missing 'no vocals': {preset!r}"
            )

    def test_suno_style_presets_horror(self):
        prompt = SunoAdapter().get_style_prompt("ai_stories_horror")
        assert "horror" in prompt.lower() or "dark" in prompt.lower()

    def test_suno_style_presets_motivation(self):
        prompt = SunoAdapter().get_style_prompt("ai_stories_motivation")
        assert "motivational" in prompt.lower() or "inspirational" in prompt.lower()


# ===========================================================================
# SunoAdapter — generate() with no API key (dry-run mode)
# ===========================================================================


class TestSunoGenerateNoKey:
    def test_suno_generate_no_key_writes_file(self):
        adapter = SunoAdapter(api_key="")
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "music.mp3"
            adapter.generate("calm piano", out)
            assert out.exists()

    def test_suno_generate_no_key_returns_path(self):
        adapter = SunoAdapter(api_key="")
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "music.mp3"
            result = adapter.generate("calm piano", out)
            assert result == out

    def test_suno_generate_no_key_creates_parent_dirs(self):
        adapter = SunoAdapter(api_key="")
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "sub" / "dir" / "music.mp3"
            adapter.generate("ambient", out)
            assert out.exists()

    def test_suno_generate_quota_exceeded_raises(self):
        adapter = SunoAdapter(api_key="sk-test", daily_limit=0)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "music.mp3"
            with pytest.raises(QuotaExceededError):
                adapter.generate("ambient", out)


# ===========================================================================
# PixabayAudioAdapter
# ===========================================================================


class TestPixabayAudioAdapter:
    def test_pixabay_no_key_not_available(self):
        assert PixabayAudioAdapter(api_key="").is_available() is False

    def test_pixabay_has_key_available(self):
        assert PixabayAudioAdapter(api_key="abc123").is_available() is True

    def test_pixabay_service_name(self):
        assert PixabayAudioAdapter(api_key="").service_name == "Pixabay Audio"

    def test_pixabay_genre_map_ghibli(self):
        assert PixabayAudioAdapter.GENRE_MAP["ghibli_asmr"] == "ambient"

    def test_pixabay_genre_map_hype(self):
        assert PixabayAudioAdapter.GENRE_MAP["hype_characters"] == "pop"

    def test_pixabay_genre_map_horror(self):
        assert PixabayAudioAdapter.GENRE_MAP["ai_stories_horror"] == "cinematic"

    def test_pixabay_generate_no_key_writes_file(self):
        adapter = PixabayAudioAdapter(api_key="")
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "track.mp3"
            adapter.generate("ambient music", out)
            assert out.exists()

    def test_pixabay_generate_no_key_returns_path(self):
        adapter = PixabayAudioAdapter(api_key="")
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "track.mp3"
            result = adapter.generate("ambient music", out)
            assert result == out

    def test_pixabay_prompt_to_genre_known(self):
        adapter = PixabayAudioAdapter()
        assert adapter._prompt_to_genre("ghibli_asmr vibes") == "ambient"

    def test_pixabay_prompt_to_genre_unknown(self):
        adapter = PixabayAudioAdapter()
        assert adapter._prompt_to_genre("completely unknown style") == "ambient"


# ===========================================================================
# SilentAudioFallback
# ===========================================================================


class TestSilentAudioFallback:
    def test_silent_fallback_always_available(self):
        assert SilentAudioFallback().is_available() is True

    def test_silent_fallback_creates_file(self):
        fb = SilentAudioFallback()
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "silent.mp3"
            p = fb.generate("anything", out)
            assert p.exists()

    def test_silent_fallback_nonzero_size(self):
        fb = SilentAudioFallback()
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "silent.mp3"
            p = fb.generate("anything", out, duration_seconds=1)
            assert p.stat().st_size > 0

    def test_silent_fallback_service_name(self):
        assert SilentAudioFallback().service_name == "Silent Fallback"

    def test_silent_fallback_returns_wav(self):
        fb = SilentAudioFallback()
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.mp3"
            p = fb.generate("test", out, duration_seconds=1)
            assert p.suffix == ".wav"
