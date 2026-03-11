"""Integration tests for EdgeTTSAdapter (Phase 2, T-102).

All TTS synthesis calls are mocked — no internet or audio libs required.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.adapters.tts.edge_tts import EdgeTTSAdapter, VOICE_MAP, select_voice


class TestSelectVoice:
    def test_uk_male(self):
        assert select_voice("uk", "male") == "uk-UA-OstapNeural"

    def test_uk_female(self):
        assert select_voice("uk", "female") == "uk-UA-PolinaNeural"

    def test_en_male(self):
        assert select_voice("en", "male") == "en-US-GuyNeural"

    def test_unknown_lang_fallback(self):
        """Unknown language falls back to English."""
        voice = select_voice("xx", "male")
        assert "en" in voice.lower() or voice == "en-US-GuyNeural"


class TestEdgeTTSAdapterSplitText:
    def test_short_text_no_split(self):
        """Text under 3000 chars returns single chunk."""
        adapter = EdgeTTSAdapter()
        chunks = adapter._split_text("Hello world.", max_chars=3000)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world."

    def test_split_at_sentence_boundary(self):
        """Text split at sentence boundaries, not mid-word."""
        adapter = EdgeTTSAdapter()
        text = "First sentence. Second sentence. Third sentence."
        chunks = adapter._split_text(text, max_chars=20)
        for chunk in chunks:
            assert len(chunk) <= 20 or "sentence" in chunk

    def test_all_chunks_under_max(self):
        """All chunks are ≤ max_chars."""
        adapter = EdgeTTSAdapter()
        text = "word " * 1000
        chunks = adapter._split_text(text, max_chars=100)
        assert all(len(c) <= 100 for c in chunks)

    def test_empty_text_returns_list_with_empty(self):
        """Empty text returns ['']."""
        adapter = EdgeTTSAdapter()
        chunks = adapter._split_text("", max_chars=100)
        assert chunks == [""]

    def test_exact_max_no_split(self):
        """Text exactly at max_chars returns single chunk."""
        adapter = EdgeTTSAdapter()
        text = "a" * 100
        chunks = adapter._split_text(text, max_chars=100)
        assert len(chunks) == 1


class TestEdgeTTSAdapterSpeak:
    def test_speak_returns_path(self, tmp_path):
        """speak() returns a Path object."""
        adapter = EdgeTTSAdapter(voice="uk-UA-OstapNeural")
        output = tmp_path / "test.mp3"

        mock_communicate = MagicMock()
        mock_communicate.save = AsyncMock()

        with patch("edge_tts.Communicate", return_value=mock_communicate):
            result = adapter.speak("Привіт!", output)

        assert isinstance(result, Path)

    def test_speak_calls_communicate_once_for_short_text(self, tmp_path):
        """Single chunk → Communicate.save() called once."""
        adapter = EdgeTTSAdapter(voice="uk-UA-OstapNeural")
        output = tmp_path / "out.mp3"
        mock_communicate = MagicMock()
        mock_communicate.save = AsyncMock()

        with patch("edge_tts.Communicate", return_value=mock_communicate) as MockComm:
            adapter.speak("Short text.", output)
            MockComm.assert_called_once_with("Short text.", "uk-UA-OstapNeural")

    def test_speak_creates_parent_dirs(self, tmp_path):
        """speak() creates parent directories if they don't exist."""
        adapter = EdgeTTSAdapter(voice="uk-UA-OstapNeural")
        output = tmp_path / "deep" / "dir" / "audio.mp3"
        mock_communicate = MagicMock()
        mock_communicate.save = AsyncMock()

        with patch("edge_tts.Communicate", return_value=mock_communicate):
            adapter.speak("Hello", output)

        assert output.parent.exists()

    def test_speak_raises_on_missing_edge_tts(self, tmp_path):
        """RuntimeError raised if edge-tts not installed."""
        adapter = EdgeTTSAdapter()
        output = tmp_path / "out.mp3"

        with patch.dict("sys.modules", {"edge_tts": None}):
            with pytest.raises(RuntimeError, match="edge-tts"):
                adapter.speak("text", output)

    def test_voice_default_ukrainian(self):
        """Default voice is Ukrainian male when no env var set."""
        import os
        old = os.environ.pop("TTS_VOICE", None)
        old_lang = os.environ.pop("TTS_LANGUAGE", None)
        try:
            adapter = EdgeTTSAdapter()
            assert "uk" in adapter.voice.lower() or "OstapNeural" in adapter.voice
        finally:
            if old:
                os.environ["TTS_VOICE"] = old
            if old_lang:
                os.environ["TTS_LANGUAGE"] = old_lang

    def test_voice_map_has_all_languages(self):
        """VOICE_MAP contains uk, en, ru, de, pl."""
        for lang in ["uk", "en", "ru", "de", "pl"]:
            assert lang in VOICE_MAP
            assert "male" in VOICE_MAP[lang]
            assert "female" in VOICE_MAP[lang]

