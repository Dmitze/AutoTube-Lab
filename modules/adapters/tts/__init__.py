"""Phase 2 — TTS adapters sub-package (Free-Tier Chain).

Free-tier TTS stack (zero cost, cloud-deployable):
────────────────────────────────────────────────────────────────────────
  Priority  Service          Limit              Notes
  ────────  ───────────────  ─────────────────  ─────────────────────
  1         edge-tts         ♾ unlimited        Microsoft Edge voices
                                                No API key. Best default.
  2         ElevenLabs       10 000 chars/month Quality voices. No CC.
  3         Gemini TTS       ~1M chars/day      Same key as LLM.
  4         TTSMaker         20 000 chars/week  Some voices unlimited.
────────────────────────────────────────────────────────────────────────

The FreeTierTTSChain auto-switches when a service's quota is exhausted.
Usage is tracked in data/quota.db (SQLite, persists between runs).

Factory (build_tts_adapter):
  TTS_CHAIN env var set → respect order in TTS_CHAIN
  Default → FreeTierTTSChain([edge-tts, +any configured services])
"""
from __future__ import annotations

from modules.adapters.tts.edge_tts import EdgeTTSAdapter
from modules.adapters.tts.free_tier_chain import FreeTierTTSChain

__all__ = [
    "EdgeTTSAdapter",
    "FreeTierTTSChain",
    "build_tts_adapter",
]


def build_tts_adapter():
    """Build the best available free-tier TTS adapter.

    Returns FreeTierTTSChain which auto-switches between services.
    Falls back to EdgeTTSAdapter (unlimited, no key) if chain fails.

    Returns
    -------
    TTSAdapter
        FreeTierTTSChain if any service configured, else EdgeTTSAdapter.

    Complexity: O(1)

    Examples
    --------
    >>> adapter = build_tts_adapter()
    >>> hasattr(adapter, 'speak')
    True
    """
    try:
        chain = FreeTierTTSChain()
        return chain
    except RuntimeError:
        # edge-tts not installed — try bare EdgeTTSAdapter
        try:
            return EdgeTTSAdapter()
        except ImportError:
            return None

