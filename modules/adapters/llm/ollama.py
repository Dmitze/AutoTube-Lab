"""Phase 2 — OllamaAdapter + LLMFallbackChain.

Roadmap tasks: T-087 through T-095 (EPIC 2.1)
Depends on:   httpx, LLMAdapter ABC, @retry

OllamaAdapter:
  Local Ollama server on VPS (http://ollama:11434).
  Requires Hetzner CX32 (8GB RAM) for llama3.2:3b (~2GB model).
  Configuration:
    OLLAMA_URL   : base URL (default: http://ollama:11434)
    OLLAMA_MODEL : model name (default: llama3.2:3b)

LLMFallbackChain:
  Chain of Responsibility pattern → O(k) where k = number of adapters.
  Order: GroqAdapter → OllamaAdapter → raise ContentGenerationError
  Logs WARNING on each fallback step.
"""
from __future__ import annotations

import logging
import os

import httpx

from modules.adapters.base import LLMAdapter
from modules.adapters.errors import NonRetryableError, RetryableError # Corrected import path
from modules.adapters.retry import exponential_backoff as retry # Correctly import retry decorator

logger = logging.getLogger(__name__)

_DEFAULT_OLLAMA_URL = "http://ollama:11434"
_DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
_REQUEST_TIMEOUT = 60.0  # Ollama can be slow on CPU


class OllamaAdapter(LLMAdapter):
    """Ollama local LLM adapter (VPS fallback).

    Parameters
    ----------
    url:
        Ollama server base URL. Falls back to ``OLLAMA_URL`` env var.
    model:
        Model name. Falls back to ``OLLAMA_MODEL`` env var.

    Complexity
    ----------
    generate(): O(tokens) — local inference, slower than Groq

    Examples
    --------
    >>> adapter = OllamaAdapter(url="http://localhost:11434")
    >>> adapter.model
    'llama3.2:3b'
    """

    def __init__(
        self,
        url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.url = (url or os.environ.get("OLLAMA_URL", _DEFAULT_OLLAMA_URL)).rstrip("/")
        self.model = model or os.environ.get("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)

    @retry(max_retries=2, base_delay=3.0, jitter=True, seed=42) # Added jitter=True for consistency
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate text via Ollama /api/generate endpoint.

        Parameters
        ----------
        prompt:
            Input prompt.
        max_tokens:
            Max tokens to generate (passed as ``num_predict``).

        Returns
        -------
        str
            Generated text.

        Raises
        ------
        RetryableError
            On connection errors or 5xx responses.
        NonRetryableError
            On 404 (model not found) or 400 errors.

        Complexity
        ----------
        O(tokens) — local CPU/GPU inference
        """
        endpoint = f"{self.url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        try:
            response = httpx.post(endpoint, json=payload, timeout=_REQUEST_TIMEOUT)
            if response.status_code == 404:
                raise NonRetryableError(
                    f"Ollama model '{self.model}' not found. "
                    f"Run: ollama pull {self.model}"
                )
            if response.status_code >= 400:
                raise RetryableError(
                    f"Ollama HTTP {response.status_code}: {response.text[:200]}"
                )
            data = response.json()
            text: str = data.get("response", "").strip()
            logger.debug(
                "Ollama generated %d chars (model=%s)", len(text), self.model
            )
            return text
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise RetryableError(f"Ollama unreachable: {exc}") from exc

    def health_check(self) -> bool:
        """Check if Ollama server is running.

        Complexity: O(1) — single HTTP HEAD request

        Returns
        -------
        bool
            True if server responds to /api/tags endpoint.
        """
        try:
            r = httpx.get(f"{self.url}/api/tags", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False


class LLMFallbackChain(LLMAdapter):
    """Chain of Responsibility for LLM adapters.

    Tries each adapter in order. Falls back to next on any exception.
    Logs WARNING on each fallback step.

    Parameters
    ----------
    adapters:
        Ordered list of LLMAdapter instances (primary first).

    Algorithm
    ---------
    Chain of Responsibility → O(k) where k = adapters tried before success.

    Examples
    --------
    >>> from modules.adapters.llm.groq import GroqAdapter
    >>> chain = LLMFallbackChain([GroqAdapter(), OllamaAdapter()])
    >>> isinstance(chain, LLMAdapter)
    True
    """

    def __init__(self, adapters: list[LLMAdapter]) -> None:
        if not adapters:
            raise ValueError("LLMFallbackChain requires at least one adapter")
        self._adapters = adapters

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Try each adapter in order; return first success.

        Parameters
        ----------
        prompt:
            Input prompt.
        max_tokens:
            Max tokens for response.

        Returns
        -------
        str
            Generated text from the first adapter that succeeds.

        Raises
        ------
        RuntimeError
            If all adapters fail.

        Complexity
        ----------
        O(k) where k = number of adapters tried before success
        """
        last_exc: Exception | None = None
        for i, adapter in enumerate(self._adapters):
            try:
                result = adapter.generate(prompt, max_tokens=max_tokens)
                if i > 0:
                    logger.info(
                        "LLMFallbackChain: succeeded with %s after %d failure(s)",
                        adapter.__class__.__name__,
                        i,
                    )
                return result
            except Exception as exc:
                logger.warning(
                    "LLMFallbackChain: %s failed (%s), trying next",
                    adapter.__class__.__name__,
                    exc,
                )
                last_exc = exc

        raise RuntimeError(
            f"All LLM adapters failed. Last error: {last_exc}"
        ) from last_exc