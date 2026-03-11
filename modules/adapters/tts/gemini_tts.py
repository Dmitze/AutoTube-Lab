"""Google Gemini TTS adapter — free tier via Gemini API.

Free tier (2026):
  Model           : gemini-2.0-flash-exp (experimental, free)
  Rate limit      : 15 req/min, 1 500 req/day (shared with LLM)
  Chars/day       : ~1 000 000 (generous)
  Commercial use  : check Google AI Studio terms

Note: Gemini TTS uses the ``generateContent`` endpoint with audio response
modality. This is the "speech" mode introduced in Gemini 2.0.

Environment variables:
  GEMINI_API_KEY    : Google AI Studio key (same as LLM)
  GEMINI_TTS_VOICE  : voice name (default: "Aoede" — warm, Ukrainian-friendly)
  GEMINI_TTS_MODEL  : model (default: gemini-2.0-flash-preview-tts)
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

import httpx

from modules.adapters.base import TTSAdapter
from ytaimbot_ml.quota.service_tracker import ServiceQuotaTracker

logger = logging.getLogger(__name__)

_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_DEFAULT_MODEL = "gemini-2.0-flash-preview-tts"
_DEFAULT_VOICE = "Aoede"   # Warm, works well with Slavic languages


class GeminiTTSAdapter(TTSAdapter):
    """Google Gemini TTS via generateContent with audio output modality.

    Uses the same free API key as GeminiLLMAdapter (GEMINI_API_KEY).
    Quota is shared with LLM requests (1500 req/day total on free tier).

    Parameters
    ----------
    api_key:
        Google AI Studio API key. Defaults to ``GEMINI_API_KEY`` env var.
    voice_name:
        Gemini voice name. Options: Aoede, Charon, Fenrir, Kore, Puck, ...
        Defaults to ``GEMINI_TTS_VOICE`` env var or "Aoede".
    quota_tracker:
        ServiceQuotaTracker for tracking usage. Created automatically if omitted.

    Complexity
    ----------
    speak(): O(len(text)) — single REST call + base64 decode

    Examples
    --------
    >>> GeminiTTSAdapter.__name__
    'GeminiTTSAdapter'
    """

    SERVICE = "gemini-tts"

    def __init__(
        self,
        api_key: str | None = None,
        voice_name: str | None = None,
        model: str | None = None,
        quota_tracker: ServiceQuotaTracker | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Get free key at https://aistudio.google.com/app/apikey"
            )
        self._voice = voice_name or os.environ.get("GEMINI_TTS_VOICE", _DEFAULT_VOICE)
        self._model = model or os.environ.get("GEMINI_TTS_MODEL", _DEFAULT_MODEL)
        self._tracker = quota_tracker or ServiceQuotaTracker()
        self._client = httpx.Client(timeout=60.0)

    def speak(self, text: str, output_path: Path) -> Path:
        """Synthesize speech using Gemini TTS and write WAV to output_path.

        Parameters
        ----------
        text:
            Text to synthesize.
        output_path:
            Destination file path (WAV format).

        Returns
        -------
        Path
            Path to generated audio file.

        Raises
        ------
        RuntimeError
            If daily quota is exhausted or API returns an error.

        Complexity: O(len(text))

        Examples
        --------
        >>> # Requires GEMINI_API_KEY
        >>> GeminiTTSAdapter.__name__
        'GeminiTTSAdapter'
        """
        chars = len(text)
        if not self._tracker.check_available(self.SERVICE, chars):
            raise RuntimeError(
                f"Gemini TTS daily quota exhausted. "
                f"Remaining: {self._tracker.remaining(self.SERVICE)} chars today."
            )

        url = _API_URL.format(model=self._model)
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": self._voice}
                    }
                },
            },
        }

        resp = self._client.post(url, json=payload, params={"key": self._api_key})

        if resp.status_code == 429:
            raise RuntimeError("Gemini TTS rate limit (429). Try again later or switch adapter.")
        resp.raise_for_status()

        data = resp.json()
        try:
            audio_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Gemini TTS response: {data}") from e

        audio_bytes = base64.b64decode(audio_b64)
        output_path = output_path.with_suffix(".wav")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_bytes)

        self._tracker.consume(self.SERVICE, chars)
        logger.info(
            "Gemini TTS: %d chars → %s (remaining: %d/day)",
            chars, output_path, self._tracker.remaining(self.SERVICE),
        )
        return output_path
