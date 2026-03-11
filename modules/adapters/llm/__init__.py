"""Phase 2 — LLM adapters sub-package.

Free-tier Cloud LLM strategy (100% zero-cost):
─────────────────────────────────────────────────────────────────────────
  Service          Free limit        Get key
  ─────────────    ─────────────     ──────────────────────────────────
  Groq Cloud       14 400 req/day    console.groq.com (no CC needed)
  Google Gemini    1 500 req/day     aistudio.google.com/app/apikey
  (Ollama)         unlimited         self-hosted only, optional VPS add-on
─────────────────────────────────────────────────────────────────────────

Priority order (build_llm_adapter):
  1. GROQ_API_KEY + GEMINI_API_KEY → LLMFallbackChain([Groq, Gemini])
  2. GROQ_API_KEY only             → GroqAdapter         (recommended default)
  3. GEMINI_API_KEY only           → GeminiAdapter
  4. OLLAMA_URL only               → OllamaAdapter       (self-hosted VPS only)
  5. None set                      → raises RuntimeError

Note on Ollama cloud: you CAN run Ollama on a free-tier cloud VM
  (Oracle Cloud Free Tier ARM - 4 OCPU, 24GB RAM) but this requires
  server setup. Groq is simpler and faster for zero-budget start.
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
    """Factory: build the best available free-tier LLMAdapter from environment.

    Priority (all free, cloud-native, no local server needed):
    ──────────────────────────────────────────────────────────
    1. GROQ_API_KEY + GEMINI_API_KEY → LLMFallbackChain([Groq→Gemini])
    2. GROQ_API_KEY only             → GroqAdapter (14 400 req/day free)
    3. GEMINI_API_KEY only           → GeminiAdapter (1 500 req/day free)
    4. OLLAMA_URL only               → OllamaAdapter (self-hosted VPS)
    5. None                          → raises RuntimeError

    Returns
    -------
    LLMAdapter
        Best available free adapter or chain.

    Raises
    ------
    RuntimeError
        If no LLM env var is set.

    Complexity
    ----------
    O(1) — env var lookups only

    Examples
    --------
    >>> import os
    >>> os.environ["GROQ_API_KEY"] = "test"
    >>> os.environ.pop("GEMINI_API_KEY", None)
    >>> adapter = build_llm_adapter()
    >>> isinstance(adapter, GroqAdapter)
    True
    """
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    ollama_url = os.environ.get("OLLAMA_URL", "").strip()

    adapters: list[LLMAdapter] = []

    if groq_key:
        adapters.append(GroqAdapter(api_key=groq_key))

    if gemini_key:
        try:
            from modules.adapters.llm.gemini import GeminiAdapter
            adapters.append(GeminiAdapter(api_key=gemini_key))
        except ImportError:
            pass  # httpx not installed yet — skip

    if not adapters and ollama_url:
        return OllamaAdapter(url=ollama_url)

    if not adapters:
        raise RuntimeError(
            "No LLM adapter configured. Set at least one of:\n"
            "  GROQ_API_KEY    — free at console.groq.com (recommended)\n"
            "  GEMINI_API_KEY  — free at aistudio.google.com/app/apikey\n"
            "  OLLAMA_URL      — self-hosted Ollama on VPS (optional)"
        )

    if len(adapters) == 1:
        return adapters[0]

    return LLMFallbackChain(adapters)


