"""SunoAdapter: AI music generation via Suno API (50 songs/day free tier).

HTTP flow:
  1. POST /generate → {"prompt": "...", "duration": N} → job_id
  2. Poll GET /feed/{job_id} until status="complete" (max 30 polls × 2s)
  3. Download MP3 from audio_url

Complexity: O(polls) where polls ≤ MAX_POLL_ATTEMPTS; all HTTP via urllib.request
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from modules.adapters.audio.base import AudioAdapter, QuotaExceededError

logger = logging.getLogger(__name__)

_BASE_URL = "https://studio-api.suno.ai/api"


class SunoAdapter(AudioAdapter):
    """Generates AI music via Suno API (50 songs/day free tier).

    Requires SUNO_API_KEY env var or api_key constructor parameter.
    Falls back gracefully when not configured (is_available() returns False).

    When api_key is empty the generate() method writes a 0-byte placeholder
    to output_path without making any network call — safe for testing.

    Parameters
    ----------
    api_key:
        Suno API key. Defaults to SUNO_API_KEY env var.
    output_dir:
        Directory to use when output_path parent does not exist.
    daily_limit:
        Override the default 50-songs/day cap.

    Complexity: O(polls) where polls ≤ MAX_POLL_ATTEMPTS

    Examples
    --------
    >>> adapter = SunoAdapter(api_key="")
    >>> adapter.is_available()
    False
    >>> adapter.service_name
    'Suno AI'
    >>> adapter.get_style_prompt("ghibli_asmr")
    'peaceful ambient piano, soft strings, Studio Ghibli style, no vocals'
    """

    MAX_DAILY_GENERATIONS: int = 50
    MAX_POLL_ATTEMPTS: int = 30
    POLL_INTERVAL_SECONDS: float = 2.0

    STYLE_PRESETS: dict[str, str] = {
        "ghibli_asmr": "peaceful ambient piano, soft strings, Studio Ghibli style, no vocals",
        "hype_characters": "upbeat anime pop, energetic, fun, catchy melody, no vocals",
        "ai_stories_horror": "dark atmospheric, tense strings, horror mood, no vocals",
        "ai_stories_drama": "emotional orchestral, piano, sad melody, no vocals",
        "ai_stories_motivation": "epic motivational, rising strings, inspirational, no vocals",
        "generic": "pleasant background music, neutral, suitable for YouTube, no vocals",
    }

    def __init__(
        self,
        api_key: str = "",
        output_dir: Path | None = None,
        daily_limit: int = MAX_DAILY_GENERATIONS,
    ) -> None:
        self._api_key: str = api_key or os.environ.get("SUNO_API_KEY", "")
        self._output_dir: Path | None = output_dir
        self._daily_limit: int = daily_limit
        self._generations_today: int = 0

    # ------------------------------------------------------------------
    # AudioAdapter interface
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        output_path: Path,
        duration_seconds: int = 60,
    ) -> Path:
        """Generate music from a text prompt and save to output_path.

        When api_key is empty (no-key mode), writes a 0-byte placeholder
        without any network call — suitable for dry-run and testing.

        When api_key is set and quota remains:
          1. POST to /generate with prompt and duration.
          2. Poll /feed/{job_id} until status == "complete".
          3. Download the MP3 from the returned audio_url.

        Parameters
        ----------
        prompt:
            Text description of the desired music style.
        output_path:
            Destination file path for the generated MP3.
        duration_seconds:
            Requested audio duration in seconds (default 60).

        Returns
        -------
        Path
            Path to the generated (or placeholder) audio file.

        Raises
        ------
        QuotaExceededError
            When the daily generation limit is reached.

        Complexity: O(MAX_POLL_ATTEMPTS) ≤ O(30) network round-trips

        Examples
        --------
        >>> from pathlib import Path
        >>> import tempfile, os
        >>> adapter = SunoAdapter(api_key="")
        >>> with tempfile.TemporaryDirectory() as d:
        ...     p = adapter.generate("calm music", Path(d) / "out.mp3")
        ...     p.exists()
        True
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._api_key:
            logger.debug("SunoAdapter: no API key — writing placeholder to %s", output_path)
            output_path.write_bytes(b"")
            return output_path

        if not self.is_available():
            raise QuotaExceededError(
                f"SunoAdapter: daily limit of {self._daily_limit} generations reached"
            )

        job_id = self._submit_generation(prompt, duration_seconds)
        audio_url = self._poll_until_complete(job_id)
        self._download(audio_url, output_path)
        self._generations_today += 1
        logger.info("SunoAdapter: generated %s → %s", prompt[:40], output_path)
        return output_path

    def is_available(self) -> bool:
        """Return True if api_key is set and daily quota has not been reached.

        Complexity: O(1)

        Examples
        --------
        >>> SunoAdapter(api_key="").is_available()
        False
        >>> SunoAdapter(api_key="sk-test").is_available()
        True
        """
        return bool(self._api_key) and self._generations_today < self._daily_limit

    @property
    def service_name(self) -> str:
        """Human-readable service name.

        Examples
        --------
        >>> SunoAdapter(api_key="").service_name
        'Suno AI'
        """
        return "Suno AI"

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_style_prompt(self, niche: str) -> str:
        """Return a curated style prompt for the given niche key.

        Falls back to 'generic' preset when the niche is not recognised.

        Parameters
        ----------
        niche:
            One of the keys in STYLE_PRESETS, e.g. "ghibli_asmr".

        Returns
        -------
        str
            Ready-to-use Suno-style music prompt.

        Complexity: O(1) dict lookup

        Examples
        --------
        >>> SunoAdapter().get_style_prompt("ghibli_asmr")
        'peaceful ambient piano, soft strings, Studio Ghibli style, no vocals'
        >>> SunoAdapter().get_style_prompt("unknown_niche")
        'pleasant background music, neutral, suitable for YouTube, no vocals'
        """
        return self.STYLE_PRESETS.get(niche, self.STYLE_PRESETS["generic"])

    # ------------------------------------------------------------------
    # Private HTTP helpers
    # ------------------------------------------------------------------

    def _submit_generation(self, prompt: str, duration_seconds: int) -> str:
        """POST /generate and return the job_id string.

        Complexity: O(1) single HTTP request
        """
        url = f"{_BASE_URL}/generate"
        payload = json.dumps(
            {"prompt": prompt, "duration": duration_seconds, "make_instrumental": True}
        ).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
                body = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                self._generations_today = self._daily_limit
                raise QuotaExceededError("SunoAdapter: 429 quota exceeded") from exc
            raise RuntimeError(f"SunoAdapter: HTTP {exc.code} on /generate") from exc

        # Suno returns a list of clip objects
        clips = body if isinstance(body, list) else body.get("clips", [body])
        if not clips:
            raise RuntimeError("SunoAdapter: empty response from /generate")
        return clips[0]["id"]

    def _poll_until_complete(self, job_id: str) -> str:
        """Poll /feed/{job_id} until status == 'complete', return audio_url.

        Complexity: O(MAX_POLL_ATTEMPTS)
        """
        url = f"{_BASE_URL}/feed/{job_id}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        for attempt in range(self.MAX_POLL_ATTEMPTS):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
                    data = json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f"SunoAdapter: HTTP {exc.code} while polling") from exc

            clips = data if isinstance(data, list) else [data]
            clip = clips[0]
            status = clip.get("status", "")
            if status == "complete":
                audio_url = clip.get("audio_url", "")
                if not audio_url:
                    raise RuntimeError("SunoAdapter: clip complete but audio_url missing")
                return audio_url
            if status == "error":
                raise RuntimeError(f"SunoAdapter: generation failed — {clip.get('error')}")

            logger.debug(
                "SunoAdapter: poll %d/%d status=%s",
                attempt + 1,
                self.MAX_POLL_ATTEMPTS,
                status,
            )
            time.sleep(self.POLL_INTERVAL_SECONDS)

        raise RuntimeError(
            f"SunoAdapter: generation timed out after {self.MAX_POLL_ATTEMPTS} polls"
        )

    def _download(self, url: str, output_path: Path) -> None:
        """Download audio from url and write to output_path.

        Complexity: O(file_size)
        """
        req = urllib.request.Request(url, headers={"User-Agent": "YTAIMBot/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:  # nosec B310
                output_path.write_bytes(resp.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"SunoAdapter: failed to download audio — HTTP {exc.code}") from exc
