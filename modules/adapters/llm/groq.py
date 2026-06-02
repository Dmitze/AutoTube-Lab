"""Phase 2 — GroqAdapter: Groq Cloud LLM adapter (primary LLM).

Roadmap tasks: T-083 through T-095 (EPIC 2.1)
Depends on:   groq SDK, LLMAdapter ABC, @retry decorator

Configuration (env vars):
  GROQ_API_KEY  : API key from console.groq.com (required)
  LLM_MODEL     : model name (default: llama-3.1-8b-instant)

Free tier limits:
  14,000 requests/day | 6,000 tokens/minute | 30 requests/minute
  Tracker: Sliding Window Counter (same pattern as YouTube QuotaTracker)

Algorithm
---------
generate() pipeline:
  1. Validate API key present              → O(1)
  2. Trim prompt to token budget guard     → O(len(prompt))
  3. POST chat.completions.create()        → O(tokens) network
  4. Extract response.choices[0].message   → O(1)
  @retry(max_retries=3, base_delay=2.0) on RetryableError (429/5xx)

Token budget guard:
  CHARS_PER_TOKEN ≈ 4 (conservative estimate for mixed-language text)
  if len(prompt) / 4 > max_prompt_tokens: truncate at word boundary
"""
from __future__ import annotations

import logging
import os

from modules.adapters.base import LLMAdapter
from modules.adapters.errors import NonRetryableError, RetryableError # Corrected import path
from modules.adapters.retry import exponential_backoff as retry # Correctly import retry decorator

logger = logging.getLogger(__name__)

# Conservative: 4 chars ≈ 1 token for Ukrainian/English mixed text
_CHARS_PER_TOKEN = 4
# Leave room for response tokens; max context window = 8192 for llama-3.1-8b-instant
_MAX_PROMPT_TOKENS = 3000


class GroqAdapter(LLMAdapter):
    """Groq Cloud LLM adapter using groq Python SDK.

    Parameters
    ----------
    model:
        Groq model identifier. Default: ``llama-3.1-8b-instant``.
    api_key:
        Groq API key. Falls back to ``GROQ_API_KEY`` env var.

    Complexity
    ----------
    generate(): O(tokens) — network I/O bound

    Examples
    --------
    >>> import os; os.environ["GROQ_API_KEY"] = "test"
    >>> adapter = GroqAdapter()
    >>> adapter.model
    'llama-3.1-8b-instant'
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or os.environ.get("LLM_MODEL", "llama-3.1-8b-instant")
        self._api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self._api_key:
            logger.warning(
                "GROQ_API_KEY not set — GroqAdapter will fail on generate()"
            )

    @retry(max_retries=3, base_delay=2.0, jitter=True, seed=42) # Added jitter=True
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate text via Groq API.

        Parameters
        ----------
        prompt:
            User-facing prompt string.
        max_tokens:
            Maximum tokens in the response (default 512).

        Returns
        -------
        str
            Generated text from the LLM.

        Raises
        ------
        NonRetryableError
            If GROQ_API_KEY is missing or response is 400/401/403.
        RetryableError
            On 429 (rate limit) or 5xx (server error).

        Complexity
        ----------
        O(tokens) — dominated by network round-trip

        Examples
        --------
        >>> # With valid GROQ_API_KEY:
        >>> adapter = GroqAdapter()
        >>> text = adapter.generate("Say hello", max_tokens=5)
        >>> isinstance(text, str)
        True
        """
        if not self._api_key:
            raise NonRetryableError("GROQ_API_KEY is not configured")

        try:
            import groq  # noqa: PLC0415
        except ImportError as exc:
            raise NonRetryableError(
                "groq package not installed: pip install groq"
            ) from exc

        safe_prompt = self._trim_prompt(prompt)

        try:
            client = groq.Groq(api_key=self._api_key)
            completion = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": safe_prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            text: str = completion.choices[0].message.content or ""
            logger.debug(
                "Groq generated %d chars (model=%s, max_tokens=%d)",
                len(text),
                self.model,
                max_tokens,
            )
            return text.strip()

        except Exception as exc:
            msg = str(exc).lower()
            if any(k in msg for k in ("429", "rate_limit", "rate limit", "too many")):
                raise RetryableError(f"Groq rate-limited: {exc}") from exc
            if any(k in msg for k in ("401", "403", "invalid_api_key", "authentication")):
                raise NonRetryableError(f"Groq auth error: {exc}") from exc
            if any(k in msg for k in ("500", "502", "503", "server")):
                raise RetryableError(f"Groq server error: {exc}") from exc
            raise RetryableError(f"Groq unknown error: {exc}") from exc

    def _trim_prompt(self, prompt: str) -> str:
        """Truncate prompt to stay within token budget.

        Algorithm: word-boundary truncation → O(n)

        Parameters
        ----------
        prompt:
            Original prompt string.

        Returns
        -------
        str
            Prompt truncated at word boundary if necessary.
        """
        max_chars = _MAX_PROMPT_TOKENS * _CHARS_PER_TOKEN
        if len(prompt) <= max_chars:
            return prompt
        truncated = prompt[:max_chars]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        logger.warning(
            "Prompt truncated: %d → %d chars (token budget guard)",
            len(prompt),
            len(truncated),
        )
        return truncated + " [...]"
