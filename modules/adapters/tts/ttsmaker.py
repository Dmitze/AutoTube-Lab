"""TTSMaker adapter — free tier (20 000 chars/week, some voices unlimited).

Free tier (2026):
  Standard voices  : 20 000 chars/week
  Unlimited voices : no hard limit (lower quality)
  API endpoint     : https://api.ttsmaker.com/v1/
  Commercial use   : allowed on free tier (check per-voice license)

Environment variables:
  TTSMAKER_API_TOKEN  : from ttsmaker.com account (free signup)
  TTSMAKER_VOICE_ID   : voice ID integer (default: 2 = US English Female)
  TTSMAKER_AUDIO_FORMAT: "mp3" | "ogg" | "aac" (default: "mp3")
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

from modules.adapters.base import TTSAdapter
from ytaimbot_ml.quota.service_tracker import ServiceQuotaTracker

logger = logging.getLogger(__name__)

_API_BASE = "https://api.ttsmaker.com/v1"
_DEFAULT_VOICE_ID = 2       # US English Female (free, 20k/week)
_UNLIMITED_VOICE_ID = 1600  # An "unlimited" voice (lower quality)


class TTSMakerAdapter(TTSAdapter):
    """TTSMaker free-tier TTS — 20 000 chars/week standard voices.

    Parameters
    ----------
    api_token:
        TTSMaker API token from ttsmaker.com.
        Defaults to ``TTSMAKER_API_TOKEN`` env var.
    voice_id:
        Integer voice ID. Defaults to 2 (US English Female).
        Use ``_UNLIMITED_VOICE_ID`` (1600) for unlimited usage.
    quota_tracker:
        ServiceQuotaTracker instance. Created automatically if omitted.

    Complexity
    ----------
    speak(): O(len(text)) — REST POST + file download

    Examples
    --------
    >>> TTSMakerAdapter.__name__
    'TTSMakerAdapter'
    """

    SERVICE = "ttsmaker"

    def __init__(
        self,
        api_token: str | None = None,
        voice_id: int | None = None,
        audio_format: str = "mp3",
        quota_tracker: ServiceQuotaTracker | None = None,
    ) -> None:
        self._token = api_token or os.environ.get("TTSMAKER_API_TOKEN", "")
        if not self._token:
            raise ValueError(
                "TTSMAKER_API_TOKEN not set. Sign up free at https://ttsmaker.com"
            )
        self._voice_id = voice_id or int(os.environ.get("TTSMAKER_VOICE_ID", str(_DEFAULT_VOICE_ID)))
        self._format = audio_format
        self._tracker = quota_tracker or ServiceQuotaTracker()
        self._client = httpx.Client(timeout=120.0)

    def speak(self, text: str, output_path: Path) -> Path:
        """Synthesize speech via TTSMaker REST API and write audio to output_path.

        Parameters
        ----------
        text:
            Text to synthesize (max 3000 chars per request).
        output_path:
            Destination audio file path.

        Returns
        -------
        Path
            Path to generated audio file.

        Raises
        ------
        RuntimeError
            If weekly quota is exhausted.

        Complexity: O(len(text))

        Examples
        --------
        >>> # Requires TTSMAKER_API_TOKEN and network access
        >>> TTSMakerAdapter.__name__
        'TTSMakerAdapter'
        """
        chars = len(text)
        if not self._tracker.check_available(self.SERVICE, chars):
            remaining = self._tracker.remaining(self.SERVICE)
            raise RuntimeError(
                f"TTSMaker weekly quota exhausted. Remaining: {remaining} chars this week."
            )

        # TTSMaker requires chunking at 3000 chars
        chunks = _chunk_text(text, max_chars=3000)
        audio_parts: list[bytes] = []

        for chunk in chunks:
            audio_data = self._synthesize_chunk(chunk)
            audio_parts.append(audio_data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"".join(audio_parts))

        self._tracker.consume(self.SERVICE, chars)
        logger.info(
            "TTSMaker TTS: %d chars → %s (remaining: %d/week)",
            chars, output_path, self._tracker.remaining(self.SERVICE),
        )
        return output_path

    def _synthesize_chunk(self, text: str) -> bytes:
        """Synthesize a single chunk via TTSMaker API.

        Step 1: POST /create-tts-order → order_id
        Step 2: GET /get-tts-order-file?token=...&order_id=... → MP3 bytes

        Complexity: O(len(text)) — two sequential HTTP calls
        """
        # Step 1: Create order
        create_resp = self._client.post(
            f"{_API_BASE}/create-tts-order",
            json={
                "token": self._token,
                "voice_id": self._voice_id,
                "ssml": "no",
                "audio_format": self._format,
                "audio_speed": 1.0,
                "audio_volume": 0,
                "text_paragraph_pause_time": 0,
                "status": 1,
                "text": text,
            },
        )
        create_resp.raise_for_status()
        order_data = create_resp.json()

        if order_data.get("status") != 200:
            raise RuntimeError(f"TTSMaker order failed: {order_data}")

        download_url = order_data["audio_file_url"]

        # Step 2: Download audio
        audio_resp = self._client.get(download_url)
        audio_resp.raise_for_status()
        return audio_resp.content


def _chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    """Split text into chunks of at most max_chars, respecting sentence boundaries.

    Complexity: O(len(text))
    """
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current = ""
    for sentence in text.replace("! ", "!|").replace(". ", ".|").replace("? ", "?|").split("|"):
        if len(current) + len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
            current = sentence
        else:
            current += " " + sentence
    if current.strip():
        chunks.append(current.strip())
    return chunks
