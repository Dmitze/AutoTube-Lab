"""Phase 2 — LLM adapters sub-package.

Adapters
--------
LLMAdapter (base)    : ABC with generate(prompt, max_tokens) → str
GroqAdapter          : Groq Cloud API (primary, llama-3.1-8b-instant, free tier)
OllamaAdapter        : Local Ollama on VPS (fallback, llama3.2:3b)
LLMFallbackChain     : Chain-of-Responsibility wrapper: Groq → Ollama → error

Factory
-------
build_llm_adapter()  : reads env vars, returns the appropriate adapter.

Selection logic (T-082):
  GROQ_API_KEY set  → GroqAdapter   (primary, 14k req/day free tier)
  OLLAMA_URL set    → OllamaAdapter (VPS fallback, requires 4GB RAM)
  Both set          → LLMFallbackChain([GroqAdapter, OllamaAdapter])
  Neither           → raises RuntimeError
"""
from __future__ import annotations

import os

from modules.adapters.base import LLMAdapter
from modules.adapters.llm.groq import GroqAdapter
from modules.adapters.llm.ollama import LLMFallbackChain, OllamaAdapter

__all__ = [
    "LLMAdapter",
    "GroqAdapter",
    "OllamaAdapter",
    "LLMFallbackChain",
    "build_llm_adapter",
]


def build_llm_adapter() -> LLMAdapter:
    """Factory: build the best available LLMAdapter from environment variables.

    Priority
    --------
    1. Both GROQ_API_KEY + OLLAMA_URL → LLMFallbackChain([Groq, Ollama])
    2. GROQ_API_KEY only              → GroqAdapter
    3. OLLAMA_URL only                → OllamaAdapter
    4. Neither                        → raises RuntimeError

    Returns
    -------
    LLMAdapter
        The configured adapter or chain.

    Raises
    ------
    RuntimeError
        If neither GROQ_API_KEY nor OLLAMA_URL is set.

    Complexity
    ----------
    O(1) — env var lookups only

    Examples
    --------
    >>> import os
    >>> os.environ["GROQ_API_KEY"] = "test"
    >>> adapter = build_llm_adapter()
    >>> isinstance(adapter, GroqAdapter)
    True
    """
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    ollama_url = os.environ.get("OLLAMA_URL", "").strip()

    if groq_key and ollama_url:
        return LLMFallbackChain([GroqAdapter(api_key=groq_key), OllamaAdapter(url=ollama_url)])
    if groq_key:
        return GroqAdapter(api_key=groq_key)
    if ollama_url:
        return OllamaAdapter(url=ollama_url)

    raise RuntimeError(
        "No LLM adapter configured. "
        "Set GROQ_API_KEY (Groq Cloud) or OLLAMA_URL (local Ollama)."
    )

