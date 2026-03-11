"""Google Gemini 1.5 Flash LLM adapter — cloud, free tier.

Free tier limits (2026):
  Model              : gemini-1.5-flash
  Requests/day       : 1 500  (via AI Studio / Generative Language API)
  Tokens/day         : 1 000 000
  Tokens/minute      : 32 000
  Context window     : 1M tokens

Environment variables:
  GEMINI_API_KEY     : Google AI Studio API key (get free at aistudio.google.com)
  GEMINI_MODEL       : override model name (default: gemini-1.5-flash)
  GEMINI_TEMPERATURE : sampling temperature 0.0–1.0 (default: 0.7)

Retry strategy (Token Bucket guard):
  429 RESOURCE_EXHAUSTED → RetryableError (exponential backoff)
  403 PERMISSION_DENIED  → NonRetryableError
  5xx                    → RetryableError
"""
from __future__ import annotations

import logging
import os
import time
from functools import wraps
from typing import Callable, TypeVar

import httpx

from modules.adapters.base import LLMAdapter

logger = logging.getLogger(__name__)

_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_DEFAULT_MODEL = "gemini-1.5-flash"
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0

F = TypeVar("F", bound=Callable)


class RetryableError(Exception):
    """Transient error — eligible for retry."""


class NonRetryableError(Exception):
    """Permanent error — do not retry."""


def _retry(func: F) -> F:
    """Exponential backoff decorator for Gemini API transient errors."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(_MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except RetryableError as e:
                if attempt == _MAX_RETRIES:
                    raise
                wait = _BACKOFF_BASE ** attempt
                logger.warning("Gemini retry %d/%d in %.1fs: %s", attempt + 1, _MAX_RETRIES, wait, e)
                time.sleep(wait)

    return wrapper  # type: ignore[return-value]


class GeminiAdapter(LLMAdapter):
    """Google Gemini 1.5 Flash LLM adapter using the Generative Language REST API.

    This adapter uses the FREE tier of Google AI Studio — no payment required.
    Get your free API key at: https://aistudio.google.com/app/apikey

    Parameters
    ----------
    api_key:
        Google AI Studio API key. Defaults to ``GEMINI_API_KEY`` env var.
    model:
        Gemini model name. Defaults to ``GEMINI_MODEL`` env var or
        ``"gemini-1.5-flash"`` (fastest, most generous free tier).
    temperature:
        Sampling temperature [0.0, 1.0]. Default 0.7.
    timeout:
        HTTP request timeout in seconds. Default 30.

    Complexity
    ----------
    generate(): O(tokens) — network I/O bound

    Examples
    --------
    >>> import os; os.environ["GEMINI_API_KEY"] = "test-key"
    >>> adapter = GeminiAdapter()
    >>> adapter.model
    'gemini-1.5-flash'
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/app/apikey"
            )
        self.model = model or os.environ.get("GEMINI_MODEL", _DEFAULT_MODEL)
        self._temperature = temperature if temperature is not None else float(
            os.environ.get("GEMINI_TEMPERATURE", "0.7")
        )
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate text using Gemini 1.5 Flash.

        Parameters
        ----------
        prompt:
            Input text prompt.
        max_tokens:
            Maximum output tokens (mapped to ``maxOutputTokens``).

        Returns
        -------
        str
            Generated text content.

        Raises
        ------
        RetryableError
            On 429 (quota) or 5xx server errors.
        NonRetryableError
            On 400 (bad request) or 403 (auth error).

        Complexity: O(tokens) — network bound

        Examples
        --------
        >>> # Requires real GEMINI_API_KEY
        >>> adapter = GeminiAdapter.__new__(GeminiAdapter)
        >>> adapter.model
        Traceback (most recent call last):
            ...
        AttributeError: 'GeminiAdapter' object has no attribute 'model'
        """
        return self._call_api(prompt, max_tokens)

    @_retry
    def _call_api(self, prompt: str, max_tokens: int) -> str:
        """Execute the Gemini REST API call with retry logic."""
        url = _API_URL.format(model=self.model)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": self._temperature,
            },
        }
        params = {"key": self._api_key}

        try:
            resp = self._client.post(url, json=payload, params=params)
        except httpx.TimeoutException as e:
            raise RetryableError(f"Gemini timeout: {e}") from e
        except httpx.NetworkError as e:
            raise RetryableError(f"Gemini network error: {e}") from e

        if resp.status_code == 200:
            data = resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                raise NonRetryableError(f"Unexpected Gemini response shape: {data}") from e

        body = resp.text
        if resp.status_code == 429 or "RESOURCE_EXHAUSTED" in body:
            raise RetryableError(f"Gemini 429 rate limit: {body[:120]}")
        if resp.status_code in (500, 502, 503, 504):
            raise RetryableError(f"Gemini {resp.status_code}: {body[:120]}")
        if resp.status_code in (400, 403) or "API_KEY_INVALID" in body:
            raise NonRetryableError(f"Gemini {resp.status_code}: {body[:200]}")

        raise RetryableError(f"Gemini unexpected status {resp.status_code}: {body[:120]}")

    def health_check(self) -> bool:
        """Ping Gemini with a minimal prompt.

        Returns
        -------
        bool
            True if the API is reachable and the key is valid.

        Complexity: O(1)

        Examples
        --------
        >>> adapter = GeminiAdapter.__new__(GeminiAdapter)
        >>> # Without real key health_check returns False
        """
        try:
            result = self._call_api("Hi", max_tokens=5)
            return bool(result)
        except Exception:
            return False
