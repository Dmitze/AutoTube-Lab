"""Unit tests for AudioChain (Chain-of-Responsibility).

All tests use no real network calls — no API keys required.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock


from modules.adapters.audio.audio_chain import AudioChain, SilentAudioFallback
from modules.adapters.audio.base import AudioAdapter, QuotaExceededError
from modules.adapters.audio.pixabay_audio import PixabayAudioAdapter
from modules.adapters.audio.suno import SunoAdapter


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_mock_adapter(
    available: bool = True,
    service_name: str = "MockAdapter",
    raises: Exception | None = None,
) -> MagicMock:
    """Return a mock AudioAdapter."""
    adapter = MagicMock(spec=AudioAdapter)
    adapter.is_available.return_value = available
    adapter.service_name = service_name
    if raises is not None:
        adapter.generate.side_effect = raises
    else:
        adapter.generate.side_effect = lambda prompt, path, duration_seconds=60: (
            path.parent.mkdir(parents=True, exist_ok=True) or path.__class__(path)
        )
    return adapter


# ---------------------------------------------------------------------------
# AudioChain core behaviour
# ---------------------------------------------------------------------------


class TestAudioChainCore:
    def test_chain_uses_first_available(self):
        """First adapter that is_available() should be used."""
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.mp3"
            a1 = _make_mock_adapter(available=True, service_name="First")
            a1.generate.return_value = out
            a2 = _make_mock_adapter(available=True, service_name="Second")
            chain = AudioChain([a1, a2])
            chain.generate("test", out)
            a1.generate.assert_called_once()
            a2.generate.assert_not_called()

    def test_chain_skips_unavailable_adapters(self):
        """Unavailable adapters should be skipped entirely."""
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.mp3"
            a1 = _make_mock_adapter(available=False, service_name="Unavailable")
            a2 = _make_mock_adapter(available=True, service_name="Available")
            a2.generate.return_value = out
            chain = AudioChain([a1, a2])
            chain.generate("test", out)
            a1.generate.assert_not_called()
            a2.generate.assert_called_once()

    def test_chain_fallback_on_quota(self):
        """QuotaExceededError should trigger fallback to next adapter."""
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.mp3"
            a1 = _make_mock_adapter(
                available=True,
                service_name="QuotaFull",
                raises=QuotaExceededError("quota"),
            )
            a2 = _make_mock_adapter(available=True, service_name="Fallback")
            a2.generate.return_value = out
            chain = AudioChain([a1, a2])
            chain.generate("test", out)
            a1.generate.assert_called_once()
            a2.generate.assert_called_once()

    def test_chain_fallback_on_runtime_error(self):
        """RuntimeError should also trigger fallback to next adapter."""
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.mp3"
            a1 = _make_mock_adapter(
                available=True,
                service_name="Broken",
                raises=RuntimeError("network error"),
            )
            a2 = _make_mock_adapter(available=True, service_name="OK")
            a2.generate.return_value = out
            chain = AudioChain([a1, a2])
            chain.generate("test", out)
            a2.generate.assert_called_once()

    def test_chain_fallback_all_unavailable(self):
        """When all real adapters are unavailable, SilentAudioFallback is used."""
        chain = AudioChain([
            SunoAdapter(api_key=""),
            PixabayAudioAdapter(api_key=""),
        ])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "music.mp3"
            result = chain.generate("peaceful music", out)
            assert result.exists()

    def test_chain_empty_adapters_uses_fallback(self):
        """AudioChain([]) should still work via SilentAudioFallback."""
        chain = AudioChain([])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "empty.mp3"
            result = chain.generate("test", out)
            assert result.exists()

    def test_chain_generate_returns_path(self):
        """generate() should return a Path that exists."""
        chain = AudioChain([])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "audio.mp3"
            result = chain.generate("ambient", out)
            assert isinstance(result, Path)
            assert result.exists()


# ---------------------------------------------------------------------------
# AudioChain — chain ordering
# ---------------------------------------------------------------------------


class TestAudioChainOrdering:
    def test_chain_order_respected(self):
        """Adapters should be tried in the order they are given."""
        call_order: list[str] = []

        def make_recording_adapter(name: str) -> MagicMock:
            adapter = MagicMock(spec=AudioAdapter)
            adapter.is_available.return_value = True
            adapter.service_name = name

            def record_call(prompt: str, path: Path, duration_seconds: int = 60) -> Path:
                call_order.append(name)
                return path

            adapter.generate.side_effect = record_call
            return adapter

        a1 = make_recording_adapter("First")
        a2 = make_recording_adapter("Second")
        chain = AudioChain([a1, a2])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.mp3"
            chain.generate("test", out)
        assert call_order[0] == "First"

    def test_chain_add_adapter(self):
        """add_adapter() should insert the adapter before SilentAudioFallback."""
        chain = AudioChain([])
        new_adapter = SunoAdapter(api_key="sk-test")
        chain.add_adapter(new_adapter, priority=0)
        assert chain.adapters[0].service_name == "Suno AI"

    def test_chain_add_adapter_default_priority(self):
        """add_adapter() with default priority inserts before SilentAudioFallback."""
        chain = AudioChain([])
        new_adapter = PixabayAudioAdapter(api_key="px-key")
        chain.add_adapter(new_adapter)
        names = [a.service_name for a in chain.adapters]
        assert names[-1] == "Silent Fallback"
        assert "Pixabay Audio" in names

    def test_silent_fallback_always_last(self):
        """SilentAudioFallback should always be the last adapter in the chain."""
        chain = AudioChain([SunoAdapter(api_key=""), PixabayAudioAdapter(api_key="")])
        assert isinstance(chain.adapters[-1], SilentAudioFallback)


# ---------------------------------------------------------------------------
# AudioChain — from_env() factory
# ---------------------------------------------------------------------------


class TestAudioChainFromEnv:
    def test_chain_default_from_env_no_keys(self, monkeypatch):
        """Without env keys, from_env() should return a working chain."""
        monkeypatch.delenv("SUNO_API_KEY", raising=False)
        monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
        chain = AudioChain.from_env()
        assert len(chain.adapters) >= 1
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "music.mp3"
            result = chain.generate("test", out)
            assert result.exists()

    def test_chain_from_env_with_suno_key(self, monkeypatch):
        """With SUNO_API_KEY set, Suno should appear first in the chain."""
        monkeypatch.setenv("SUNO_API_KEY", "sk-test-key")
        monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
        chain = AudioChain.from_env()
        assert chain.adapters[0].service_name == "Suno AI"

    def test_chain_from_env_with_pixabay_key(self, monkeypatch):
        """With PIXABAY_API_KEY set (no Suno key), Pixabay should be first real adapter."""
        monkeypatch.delenv("SUNO_API_KEY", raising=False)
        monkeypatch.setenv("PIXABAY_API_KEY", "px-test-key")
        chain = AudioChain.from_env()
        names = [a.service_name for a in chain.adapters]
        assert "Pixabay Audio" in names


# ---------------------------------------------------------------------------
# QuotaExceededError
# ---------------------------------------------------------------------------


class TestQuotaExceededError:
    def test_quota_exceeded_error_is_exception(self):
        assert issubclass(QuotaExceededError, Exception)

    def test_quota_exceeded_error_message(self):
        err = QuotaExceededError("daily limit reached")
        assert "daily limit" in str(err)
