"""FreeTierTTSChain: Chain-of-Responsibility for free-tier TTS services.

Priority chain (best quality → unlimited fallback):
  1. ElevenLabs    — 10 000 chars/month  (best quality, commercial ❌ on free)
  2. GeminiTTS     — ~1M chars/day       (good quality, commercial ✅)
  3. TTSMaker      — 20 000 chars/week   (decent quality, commercial ✅)
  4. edge-tts      — unlimited           (good quality, commercial ✅, offline-ish)

Algorithm — Chain of Responsibility:
  For each adapter in priority order:
    1. Check ServiceQuotaTracker.check_available(service, len(text))
    2. If available → attempt speak()
    3. If RuntimeError (quota/auth) → log + try next adapter
    4. If all fail → raise RuntimeError with summary

Environment variables that control the chain:
  TTS_CHAIN          : comma-separated service names to override order
                       e.g. "elevenlabs,gemini-tts,edge-tts"
  TTS_QUALITY_MODE   : "quality" (default) | "fast" (skip ElevenLabs)
  TTS_SKIP_SERVICES  : comma-separated services to exclude from chain

Complexity: O(n) per call, n = number of adapters tried (worst case 4)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from modules.adapters.base import TTSAdapter
from ytaimbot_ml.quota.service_tracker import ServiceQuotaTracker

logger = logging.getLogger(__name__)


def _build_default_chain(
    tracker: ServiceQuotaTracker | None = None,
) -> list[tuple[str, TTSAdapter]]:
    """Build the ordered list of (service_name, adapter) pairs.

    Only includes adapters whose API keys are available in env.
    edge-tts is always included last (no key required).

    Complexity: O(1)
    """
    tracker = tracker or ServiceQuotaTracker()
    chain: list[tuple[str, TTSAdapter]] = []
    skip = set(os.environ.get("TTS_SKIP_SERVICES", "").split(","))

    # 1. ElevenLabs — highest quality
    if "elevenlabs" not in skip and os.environ.get("ELEVENLABS_API_KEY", "").strip():
        try:
            from modules.adapters.tts.elevenlabs import ElevenLabsTTSAdapter
            chain.append(("elevenlabs", ElevenLabsTTSAdapter(quota_tracker=tracker)))
            logger.debug("TTS chain: ElevenLabs added")
        except Exception as e:
            logger.debug("TTS chain: ElevenLabs skipped (%s)", e)

    # 2. Gemini TTS — generous daily free tier
    if "gemini-tts" not in skip and os.environ.get("GEMINI_API_KEY", "").strip():
        try:
            from modules.adapters.tts.gemini_tts import GeminiTTSAdapter
            chain.append(("gemini-tts", GeminiTTSAdapter(quota_tracker=tracker)))
            logger.debug("TTS chain: GeminiTTS added")
        except Exception as e:
            logger.debug("TTS chain: GeminiTTS skipped (%s)", e)

    # 3. TTSMaker — 20k chars/week
    if "ttsmaker" not in skip and os.environ.get("TTSMAKER_API_TOKEN", "").strip():
        try:
            from modules.adapters.tts.ttsmaker import TTSMakerAdapter
            chain.append(("ttsmaker", TTSMakerAdapter(quota_tracker=tracker)))
            logger.debug("TTS chain: TTSMaker added")
        except Exception as e:
            logger.debug("TTS chain: TTSMaker skipped (%s)", e)

    # 4. edge-tts — unlimited, always available (Microsoft Edge voices)
    if "edge-tts" not in skip:
        try:
            from modules.adapters.tts.edge_tts import EdgeTTSAdapter
            chain.append(("edge-tts", EdgeTTSAdapter()))
            logger.debug("TTS chain: edge-tts added (unlimited fallback)")
        except ImportError:
            logger.warning("TTS chain: edge-tts not installed — install with: pip install edge-tts")

    return chain


class FreeTierTTSChain(TTSAdapter):
    """Chain-of-Responsibility TTS adapter that auto-switches on quota exhaustion.

    Iterates through free-tier TTS services in quality order, automatically
    falling back to the next service when quota is exhausted or an error occurs.
    Always ends with edge-tts as an unlimited fallback.

    Parameters
    ----------
    chain:
        Ordered list of (service_name, TTSAdapter) tuples.
        Auto-built from environment if not provided.
    tracker:
        Shared ServiceQuotaTracker. Auto-created if not provided.

    Complexity
    ----------
    speak(): O(n) worst-case n = chain length, O(1) typical (first adapter succeeds)

    Examples
    --------
    >>> chain = FreeTierTTSChain()
    >>> len(chain.adapters) >= 1  # at least edge-tts
    True
    """

    def __init__(
        self,
        chain: list[tuple[str, TTSAdapter]] | None = None,
        tracker: ServiceQuotaTracker | None = None,
    ) -> None:
        self._tracker = tracker or ServiceQuotaTracker()
        self._chain = chain if chain is not None else _build_default_chain(self._tracker)
        if not self._chain:
            raise RuntimeError(
                "FreeTierTTSChain: no TTS adapters available. "
                "Install edge-tts: pip install edge-tts"
            )

    @property
    def adapters(self) -> list[tuple[str, TTSAdapter]]:
        """Ordered list of (service_name, adapter) in the chain."""
        return self._chain

    def speak(self, text: str, output_path: Path) -> Path:
        """Synthesize speech, auto-switching services on quota exhaustion.

        Tries each adapter in chain order. On any RuntimeError (quota, auth,
        network), logs a warning and tries the next adapter. Raises only if
        ALL adapters fail.

        Parameters
        ----------
        text:
            Text to synthesize.
        output_path:
            Destination audio file path.

        Returns
        -------
        Path
            Path to generated audio file (from the adapter that succeeded).

        Raises
        ------
        RuntimeError
            If all adapters in the chain fail.

        Complexity: O(n) worst case, O(1) typical

        Examples
        --------
        >>> from pathlib import Path
        >>> chain = FreeTierTTSChain()
        >>> hasattr(chain, 'speak')
        True
        """
        errors: list[str] = []
        chars = len(text)

        for service_name, adapter in self._chain:
            # Pre-check quota before attempting (fast path)
            if not self._tracker.check_available(service_name, chars):
                remaining = self._tracker.remaining(service_name)
                logger.info(
                    "TTS chain: %s quota exhausted (%d remaining), skipping",
                    service_name, remaining,
                )
                errors.append(f"{service_name}: quota exhausted ({remaining} remaining)")
                continue

            try:
                result = adapter.speak(text, output_path)
                logger.info("TTS chain: used %s for %d chars", service_name, chars)
                return result
            except Exception as exc:  # noqa: BLE001
                logger.warning("TTS chain: %s failed — %s", service_name, exc)
                errors.append(f"{service_name}: {exc}")
                continue

        raise RuntimeError(
            f"FreeTierTTSChain: all {len(self._chain)} adapters failed.\n"
            + "\n".join(f"  • {e}" for e in errors)
        )

    def quota_summary(self) -> dict[str, dict]:
        """Return free-tier quota status for all services in the chain.

        Returns
        -------
        dict[str, dict]
            Keys: service name. Values: {used, limit, remaining, period_days}.

        Complexity: O(n)

        Examples
        --------
        >>> chain = FreeTierTTSChain()
        >>> isinstance(chain.quota_summary(), dict)
        True
        """
        summary = self._tracker.summary()
        return {
            service: summary.get(service, {"remaining": -1})
            for service, _ in self._chain
        }
