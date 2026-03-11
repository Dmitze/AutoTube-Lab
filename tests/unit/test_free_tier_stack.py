"""Tests for Phase 5b free-tier stack:
  - ServiceQuotaTracker (SQLite-backed quota tracking)
  - GeminiAdapter (cloud LLM, mocked)
  - FreeTierTTSChain (Chain-of-Responsibility auto-switch)
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ytaimbot_ml.quota.service_tracker import ServiceQuotaTracker, _SERVICE_DEFAULTS


# ===========================================================================
# ServiceQuotaTracker tests (pure SQLite — no network)
# ===========================================================================


class TestServiceQuotaTracker:
    def _tracker(self) -> ServiceQuotaTracker:
        return ServiceQuotaTracker(db_path=":memory:")

    def test_default_services_seeded(self):
        t = self._tracker()
        summary = t.summary()
        assert "edge-tts" in summary
        assert "elevenlabs" in summary
        assert "groq-llm" in summary

    def test_edge_tts_is_unlimited(self):
        t = self._tracker()
        assert t.check_available("edge-tts", 99999)
        assert t.remaining("edge-tts") == -1

    def test_elevenlabs_initial_full(self):
        t = self._tracker()
        assert t.remaining("elevenlabs") == 10_000

    def test_check_available_true_within_limit(self):
        t = self._tracker()
        assert t.check_available("elevenlabs", 500)

    def test_check_available_false_over_limit(self):
        t = self._tracker()
        t.consume("elevenlabs", 10_000)
        assert not t.check_available("elevenlabs", 1)

    def test_consume_reduces_remaining(self):
        t = self._tracker()
        t.consume("elevenlabs", 1000)
        assert t.remaining("elevenlabs") == 9_000

    def test_consume_multiple_times(self):
        t = self._tracker()
        t.consume("elevenlabs", 3000)
        t.consume("elevenlabs", 2000)
        assert t.remaining("elevenlabs") == 5_000

    def test_reset_service_restores_full(self):
        t = self._tracker()
        t.consume("elevenlabs", 5000)
        t.reset_service("elevenlabs")
        assert t.remaining("elevenlabs") == 10_000

    def test_unknown_service_allows_by_default(self):
        t = self._tracker()
        assert t.check_available("unknown-service-xyz", 1)

    def test_groq_llm_daily_limit(self):
        t = self._tracker()
        assert t.remaining("groq-llm") == 14_400

    def test_gemini_llm_daily_limit(self):
        t = self._tracker()
        assert t.remaining("gemini-llm") == 1_500

    def test_ttsmaker_weekly_limit(self):
        t = self._tracker()
        assert t.remaining("ttsmaker") == 20_000

    def test_summary_returns_all_services(self):
        t = self._tracker()
        summary = t.summary()
        for svc in _SERVICE_DEFAULTS:
            assert svc in summary

    def test_consume_unlimited_service_noops(self):
        t = self._tracker()
        t.consume("edge-tts", 999999)
        assert t.remaining("edge-tts") == -1


# ===========================================================================
# GeminiAdapter tests (mocked HTTP — no real API calls)
# ===========================================================================


class TestGeminiAdapter:
    def _make_adapter(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            from modules.adapters.llm.gemini import GeminiAdapter
            return GeminiAdapter(api_key="test-key")

    def test_adapter_init(self):
        adapter = self._make_adapter()
        assert adapter.model == "gemini-1.5-flash"
        assert adapter._api_key == "test-key"

    def test_generate_success(self):
        adapter = self._make_adapter()
        mock_response = {
            "candidates": [{"content": {"parts": [{"text": "Hello from Gemini"}]}}]
        }
        with patch.object(adapter._client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
            )
            result = adapter.generate("Say hello", max_tokens=10)
        assert result == "Hello from Gemini"

    def test_generate_429_raises_retryable(self):
        from modules.adapters.llm.gemini import RetryableError
        adapter = self._make_adapter()
        with patch.object(adapter._client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=429,
                text="RESOURCE_EXHAUSTED",
            )
            with pytest.raises((RetryableError, RuntimeError)):
                adapter._call_api("test", 10)

    def test_generate_403_raises_non_retryable(self):
        from modules.adapters.llm.gemini import NonRetryableError
        adapter = self._make_adapter()
        with patch.object(adapter._client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=403,
                text="API_KEY_INVALID",
            )
            with pytest.raises((NonRetryableError, RuntimeError)):
                adapter._call_api("test", 10)

    def test_missing_api_key_raises_value_error(self):
        with patch.dict("os.environ", {}, clear=True):
            from modules.adapters.llm.gemini import GeminiAdapter
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                GeminiAdapter()

    def test_health_check_returns_bool(self):
        adapter = self._make_adapter()
        mock_response = {
            "candidates": [{"content": {"parts": [{"text": "ok"}]}}]
        }
        with patch.object(adapter._client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
            )
            assert adapter.health_check() is True

    def test_health_check_returns_false_on_error(self):
        adapter = self._make_adapter()
        with patch.object(adapter._client, "post") as mock_post:
            mock_post.side_effect = Exception("network error")
            assert adapter.health_check() is False


# ===========================================================================
# FreeTierTTSChain tests
# ===========================================================================


class MockTTSAdapter:
    """Mock TTS adapter for testing the chain."""

    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.calls: list[str] = []

    def speak(self, text: str, output_path: Path) -> Path:
        self.calls.append(text)
        if self.should_fail:
            raise RuntimeError(f"{self.name} failed")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"audio from {self.name}")
        return output_path


class TestFreeTierTTSChain:
    def _chain(self, adapters, tracker=None):
        from modules.adapters.tts.free_tier_chain import FreeTierTTSChain
        tracker = tracker or ServiceQuotaTracker(db_path=":memory:")
        chain_list = [(a.name, a) for a in adapters]
        return FreeTierTTSChain(chain=chain_list, tracker=tracker)

    def test_uses_first_adapter(self, tmp_path):
        a1 = MockTTSAdapter("svc-a")
        a2 = MockTTSAdapter("svc-b")
        chain = self._chain([a1, a2])
        result = chain.speak("hello", tmp_path / "out.mp3")
        assert a1.calls == ["hello"]
        assert a2.calls == []

    def test_falls_back_when_first_fails(self, tmp_path):
        a1 = MockTTSAdapter("svc-a", should_fail=True)
        a2 = MockTTSAdapter("svc-b")
        chain = self._chain([a1, a2])
        result = chain.speak("hello", tmp_path / "out.mp3")
        assert a2.calls == ["hello"]

    def test_raises_when_all_fail(self, tmp_path):
        from modules.adapters.tts.free_tier_chain import FreeTierTTSChain
        a1 = MockTTSAdapter("svc-a", should_fail=True)
        a2 = MockTTSAdapter("svc-b", should_fail=True)
        chain = self._chain([a1, a2])
        with pytest.raises(RuntimeError, match="all"):
            chain.speak("hello", tmp_path / "out.mp3")

    def test_skips_exhausted_quota_service(self, tmp_path):
        tracker = ServiceQuotaTracker(db_path=":memory:")
        # Register custom service with 0 limit
        tracker._conn.execute(
            "INSERT INTO service_quota (service, used, period_limit, period_days, period_start) "
            "VALUES ('svc-limited', 100, 100, 30, date('now'))"
        )
        tracker._conn.commit()

        a1 = MockTTSAdapter("svc-limited")
        a2 = MockTTSAdapter("svc-unlimited")
        chain = self._chain([a1, a2], tracker=tracker)
        chain.speak("hello", tmp_path / "out.mp3")
        # a1 was skipped due to quota exhaustion
        assert a1.calls == []
        assert a2.calls == ["hello"]

    def test_quota_summary_returns_dict(self):
        a1 = MockTTSAdapter("edge-tts")
        chain = self._chain([a1])
        summary = chain.quota_summary()
        assert isinstance(summary, dict)
        assert "edge-tts" in summary

    def test_adapters_property(self):
        a1 = MockTTSAdapter("svc-a")
        a2 = MockTTSAdapter("svc-b")
        chain = self._chain([a1, a2])
        assert len(chain.adapters) == 2

    def test_empty_chain_raises(self):
        from modules.adapters.tts.free_tier_chain import FreeTierTTSChain
        with pytest.raises(RuntimeError):
            FreeTierTTSChain(chain=[])

    def test_returns_output_path(self, tmp_path):
        a1 = MockTTSAdapter("svc-a")
        chain = self._chain([a1])
        result = chain.speak("hi", tmp_path / "audio.mp3")
        assert isinstance(result, Path)


# ===========================================================================
# PexelsStockAdapter tests (no network)
# ===========================================================================


class TestPexelsStockAdapter:
    def test_no_keys_returns_empty(self):
        from modules.adapters.video.pexels import PexelsStockAdapter
        adapter = PexelsStockAdapter(pexels_key="", pixabay_key="")
        result = adapter.fetch_for_plan(["python"])
        assert result == []

    def test_empty_keywords_returns_empty(self):
        from modules.adapters.video.pexels import PexelsStockAdapter
        adapter = PexelsStockAdapter(pexels_key="fake")
        result = adapter.search([])
        assert result == []

    def test_stock_video_is_hd(self):
        from modules.adapters.video.pexels import StockVideo
        v = StockVideo("1", "https://x.mp4", "", 1920, 1080, 10, "pexels")
        assert v.is_hd is True

    def test_stock_video_not_hd(self):
        from modules.adapters.video.pexels import StockVideo
        v = StockVideo("1", "https://x.mp4", "", 640, 480, 10, "pexels")
        assert v.is_hd is False

    def test_search_pexels_api_error_returns_empty(self):
        from modules.adapters.video.pexels import PexelsStockAdapter
        adapter = PexelsStockAdapter(pexels_key="bad-key")
        with patch.object(adapter._client, "get") as mock_get:
            mock_get.side_effect = Exception("network error")
            result = adapter.search(["python"])
        assert result == []
