"""Phase 2 — LLMAdapter ABC: interface for all LLM adapters.

Roadmap tasks: T-082 (EPIC 2.1)
Used by:      GroqAdapter, OllamaAdapter, ScriptGenerator

Status: 🔲 Pending — T-082 (Phase 2)
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    """Abstract base class for LLM text generation adapters.

    All implementations MUST:
    - Accept a prompt string, return generated text
    - Respect token budget (max_tokens parameter)
    - Implement retry logic via @retry decorator
    - Fall back gracefully on quota/network errors

    Complexity: generate() → O(tokens) network I/O
    """

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate text from prompt.

        Parameters
        ----------
        prompt:
            Input prompt string.
        max_tokens:
            Maximum tokens to generate.

        Returns
        -------
        str
            Generated text.

        Raises
        ------
        RetryableError
            On 429 / 5xx responses.
        NonRetryableError
            On 400 / 403 responses.
        """
        ...  # pragma: no cover
