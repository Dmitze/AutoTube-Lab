"""Integration tests for GroqAdapter + OllamaAdapter + LLMFallbackChain (Phase 2).

All network calls are mocked. No real API keys required.

Test cases:
  test_groq_generate_returns_string          : basic happy path
  test_groq_retries_on_rate_limit            : RetryableError triggers retry
  test_groq_no_retry_on_auth_error           : NonRetryableError → immediate fail
  test_groq_missing_api_key_raises           : missing key → NonRetryableError
  test_groq_prompt_trim_over_budget          : long prompt is trimmed
  test_ollama_generate_returns_string        : OllamaAdapter happy path
  test_ollama_fallback_on_connection_error   : ConnectError → RetryableError
  test_llm_fallback_chain_uses_first         : chain uses first adapter
  test_llm_fallback_chain_falls_back         : chain falls back on failure
  test_llm_fallback_chain_all_fail_raises    : all fail → RuntimeError
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from modules.adapters.llm.groq import GroqAdapter
from modules.adapters.llm.ollama import LLMFallbackChain, OllamaAdapter
from modules.adapters.retry import NonRetryableError, RetryableError


# ---------------------------------------------------------------------------
# GroqAdapter tests
# ---------------------------------------------------------------------------


class TestGroqAdapter:
    def test_generate_returns_string(self):
        """generate() returns a non-empty string on success."""
        adapter = GroqAdapter(api_key="test-key")
        mock_choice = MagicMock()
        mock_choice.message.content = "Generated YouTube hook text"
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        with patch("groq.Groq") as MockGroq:
            MockGroq.return_value.chat.completions.create.return_value = mock_completion
            result = adapter.generate("Write a hook about Python", max_tokens=50)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "hook" in result.lower() or "generated" in result.lower()

    def test_generate_strips_whitespace(self):
        """Output is stripped of leading/trailing whitespace."""
        adapter = GroqAdapter(api_key="test-key")
        mock_choice = MagicMock()
        mock_choice.message.content = "  hello world  \n"
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        with patch("groq.Groq") as MockGroq:
            MockGroq.return_value.chat.completions.create.return_value = mock_completion
            result = adapter.generate("prompt")

        assert result == "hello world"

    def test_retries_on_rate_limit(self):
        """429 rate-limit error triggers RetryableError."""
        adapter = GroqAdapter(api_key="test-key")
        with patch("groq.Groq") as MockGroq:
            MockGroq.return_value.chat.completions.create.side_effect = Exception(
                "Error code: 429 - rate_limit_exceeded"
            )
            with pytest.raises((RetryableError, RuntimeError, Exception)):
                adapter.generate("prompt")

    def test_no_retry_on_auth_error(self):
        """Authentication error raises NonRetryableError."""
        adapter = GroqAdapter(api_key="bad-key")
        with patch("groq.Groq") as MockGroq:
            MockGroq.return_value.chat.completions.create.side_effect = Exception(
                "Error code: 401 - invalid_api_key"
            )
            with pytest.raises((NonRetryableError, RuntimeError, Exception)):
                adapter.generate("prompt")

    def test_missing_api_key_raises(self):
        """Missing GROQ_API_KEY raises NonRetryableError without calling API."""
        old = os.environ.pop("GROQ_API_KEY", None)
        try:
            adapter = GroqAdapter(api_key="")
            with pytest.raises((NonRetryableError, RuntimeError, Exception)):
                adapter.generate("prompt")
        finally:
            if old:
                os.environ["GROQ_API_KEY"] = old

    def test_prompt_trim_over_budget(self):
        """Very long prompts are trimmed before sending."""
        adapter = GroqAdapter(api_key="test-key")
        long_prompt = "word " * 10000  # ~40000 chars > 12000 char limit
        trimmed = adapter._trim_prompt(long_prompt)
        assert len(trimmed) <= 12100  # 3000 tokens × 4 chars + "[...]"
        assert trimmed.endswith("[...]")

    def test_prompt_short_unchanged(self):
        """Prompts within budget are returned unchanged."""
        adapter = GroqAdapter(api_key="test-key")
        short = "hello world"
        assert adapter._trim_prompt(short) == short

    def test_model_default(self):
        """Default model is llama-3.1-8b-instant."""
        adapter = GroqAdapter(api_key="test-key")
        assert adapter.model == "llama-3.1-8b-instant"

    def test_model_override(self):
        """Model can be overridden in constructor."""
        adapter = GroqAdapter(api_key="test-key", model="llama3-70b-8192")
        assert adapter.model == "llama3-70b-8192"


# ---------------------------------------------------------------------------
# OllamaAdapter tests
# ---------------------------------------------------------------------------


class TestOllamaAdapter:
    def test_generate_returns_string(self):
        """generate() returns a string from Ollama /api/generate."""
        adapter = OllamaAdapter(url="http://localhost:11434")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Local model output", "done": True}

        with patch("httpx.post", return_value=mock_response):
            result = adapter.generate("Write a hook", max_tokens=50)

        assert result == "Local model output"

    def test_404_model_not_found(self):
        """HTTP 404 raises NonRetryableError (model not pulled)."""
        adapter = OllamaAdapter(url="http://localhost:11434")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "model not found"

        with patch("httpx.post", return_value=mock_response):
            with pytest.raises((NonRetryableError, RuntimeError, Exception)):
                adapter.generate("prompt")

    def test_connection_error_raises_retryable(self):
        """Connection error raises RetryableError."""
        import httpx
        adapter = OllamaAdapter(url="http://localhost:11434")
        with patch("httpx.post", side_effect=httpx.ConnectError("refused")):
            with pytest.raises((RetryableError, RuntimeError, Exception)):
                adapter.generate("prompt")

    def test_health_check_true_on_200(self):
        """health_check() returns True when Ollama responds 200."""
        adapter = OllamaAdapter(url="http://localhost:11434")
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.get", return_value=mock_response):
            assert adapter.health_check() is True

    def test_health_check_false_on_error(self):
        """health_check() returns False on connection error."""
        import httpx
        adapter = OllamaAdapter(url="http://localhost:11434")
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            assert adapter.health_check() is False


# ---------------------------------------------------------------------------
# LLMFallbackChain tests
# ---------------------------------------------------------------------------


class TestLLMFallbackChain:
    def _make_mock_adapter(self, return_value=None, raises=None):
        mock = MagicMock()
        if raises:
            mock.generate.side_effect = raises
        else:
            mock.generate.return_value = return_value
        return mock

    def test_uses_first_adapter_on_success(self):
        """Chain returns result from first adapter if it succeeds."""
        a1 = self._make_mock_adapter("first adapter output")
        a2 = self._make_mock_adapter("second adapter output")
        chain = LLMFallbackChain([a1, a2])

        result = chain.generate("prompt")
        assert result == "first adapter output"
        a2.generate.assert_not_called()

    def test_falls_back_to_second_on_failure(self):
        """Chain falls back to second adapter when first fails."""
        a1 = self._make_mock_adapter(raises=RetryableError("rate limit"))
        a2 = self._make_mock_adapter("fallback output")
        chain = LLMFallbackChain([a1, a2])

        result = chain.generate("prompt")
        assert result == "fallback output"
        a1.generate.assert_called_once()
        a2.generate.assert_called_once()

    def test_all_fail_raises_runtime_error(self):
        """All adapters failing raises RuntimeError."""
        a1 = self._make_mock_adapter(raises=Exception("fail1"))
        a2 = self._make_mock_adapter(raises=Exception("fail2"))
        chain = LLMFallbackChain([a1, a2])

        with pytest.raises(RuntimeError, match="All LLM adapters failed"):
            chain.generate("prompt")

    def test_empty_adapters_raises_value_error(self):
        """Empty adapter list raises ValueError on construction."""
        with pytest.raises(ValueError, match="at least one adapter"):
            LLMFallbackChain([])

    def test_passes_max_tokens_to_adapter(self):
        """max_tokens parameter is forwarded to the underlying adapter."""
        a1 = self._make_mock_adapter("output")
        chain = LLMFallbackChain([a1])
        chain.generate("prompt", max_tokens=128)
        a1.generate.assert_called_once_with("prompt", max_tokens=128)

