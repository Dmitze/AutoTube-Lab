"""ElevenLabs TTS adapter — free tier (10 000 chars/month).

Free tier (2026):
  Plan           : Free (no credit card)
  Characters     : 10 000 / month
  Commercial use : NOT allowed on free tier (personal use only)
  Voices         : 3 preset + community voices
  API endpoint   : POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}

Environment variables:
  ELEVENLABS_API_KEY  : from elevenlabs.io profile settings
  ELEVENLABS_VOICE_ID : voice ID (default: EXAVITQu4vr4xnSDxMaL = "Bella", multilingual)
  ELEVENLABS_MODEL    : model ID (default: eleven_multilingual_v2)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

from modules.adapters.base import TTSAdapter
from ytaimbot_ml.quota.service_tracker import ServiceQuotaTracker

logger = logging.getLogger(__name__)

_API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
_DEFAULT_VOICE = "EXAVITQu4vr4xnSDxMaL"   # "Bella" — multilingual v2
_DEFAULT_MODEL = "eleven_multilingual_v2"


class ElevenLabsTTSAdapter(TTSAdapter):
    """ElevenLabs TTS — highest quality, 10 000 chars/month free.

    Parameters
    ----------
    api_key:
        ElevenLabs API key. Defaults to ``ELEVENLABS_API_KEY`` env var.
    voice_id:
        ElevenLabs voice ID. Defaults to ``ELEVENLABS_VOICE_ID`` or Bella.
    quota_tracker:
        ServiceQuotaTracker instance. Created automatically if omitted.

    Complexity
    ----------
    speak(): O(len(text)) — network I/O bound

    Examples
    --------
    >>> adapter = ElevenLabsTTSAdapter.__new__(ElevenLabsTTSAdapter)
    >>> # requires ELEVENLABS_API_KEY
    """

    SERVICE = "elevenlabs"

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None,
        model: str | None = None,
        quota_tracker: ServiceQuotaTracker | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY not set. Sign up free at https://elevenlabs.io"
            )
        self._voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID", _DEFAULT_VOICE)
        self._model = model or os.environ.get("ELEVENLABS_MODEL", _DEFAULT_MODEL)
        self._tracker = quota_tracker or ServiceQuotaTracker()
        self._client = httpx.Client(timeout=60.0)

    def speak(self, text: str, output_path: Path) -> Path:
        """Synthesize speech with ElevenLabs and write MP3 to output_path.

        Parameters
        ----------
        text:
            Text to synthesize.
        output_path:
            Destination MP3 file path.

        Returns
        -------
        Path
            Path to the generated audio file.

        Raises
        ------
        RuntimeError
            If monthly quota is exhausted.
        ValueError
            If API key is invalid (401).

        Complexity: O(len(text))

        Examples
        --------
        >>> # Requires ELEVENLABS_API_KEY and network access
        >>> adapter = ElevenLabsTTSAdapter.__new__(ElevenLabsTTSAdapter)
        """
        chars = len(text)
        if not self._tracker.check_available(self.SERVICE, chars):
            remaining = self._tracker.remaining(self.SERVICE)
            raise RuntimeError(
                f"ElevenLabs free quota exhausted. "
                f"Remaining: {remaining} chars this month. "
                f"Resets in {self._tracker.summary().get(self.SERVICE, {}).get('period_days', 30)} days."
            )

        url = _API_URL.format(voice_id=self._voice_id)
        payload = {
            "text": text,
            "model_id": self._model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        resp = self._client.post(url, json=payload, headers=headers)

        if resp.status_code == 401:
            raise ValueError("ElevenLabs API key invalid (401). Check ELEVENLABS_API_KEY.")
        if resp.status_code == 429:
            raise RuntimeError("ElevenLabs rate limit (429). Quota likely exhausted.")
        resp.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(resp.content)

        self._tracker.consume(self.SERVICE, chars)
        logger.info(
            "ElevenLabs TTS: %d chars → %s (remaining: %d/month)",
            chars, output_path, self._tracker.remaining(self.SERVICE),
        )
        return output_path
