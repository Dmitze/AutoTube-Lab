"""PixabayAudioAdapter: free-use music downloads via Pixabay Audio API.

Free tier: 100 req/min, 5000/day. Commercial use allowed.
Requires PIXABAY_API_KEY env var (free registration at pixabay.com).

Complexity: O(1) search + O(file_size) download
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from modules.adapters.audio.base import AudioAdapter, QuotaExceededError

logger = logging.getLogger(__name__)


class PixabayAudioAdapter(AudioAdapter):
    """Downloads free-use music from Pixabay Audio API.

    Free tier: 100 req/min, 5000/day. Commercial use allowed.
    Requires PIXABAY_API_KEY env var or api_key constructor parameter.

    When api_key is empty, is_available() returns False and generate()
    writes a 0-byte placeholder — no network calls made.

    Parameters
    ----------
    api_key:
        Pixabay API key. Defaults to PIXABAY_API_KEY env var.
    output_dir:
        Optional default output directory.

    Complexity: O(1) search + O(file_size) download

    Examples
    --------
    >>> adapter = PixabayAudioAdapter(api_key="")
    >>> adapter.is_available()
    False
    >>> adapter.service_name
    'Pixabay Audio'
    """

    BASE_URL: str = "https://pixabay.com/api/music/"

    GENRE_MAP: dict[str, str] = {
        "ghibli_asmr": "ambient",
        "hype_characters": "pop",
        "ai_stories_horror": "cinematic",
        "ai_stories_drama": "classical",
        "ai_stories_motivation": "cinematic",
        "generic": "ambient",
    }

    def __init__(
        self,
        api_key: str = "",
        output_dir: Path | None = None,
    ) -> None:
        self._api_key: str = api_key or os.environ.get("PIXABAY_API_KEY", "")
        self._output_dir: Path | None = output_dir

    # ------------------------------------------------------------------
    # AudioAdapter interface
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        output_path: Path,
        duration_seconds: int = 60,
    ) -> Path:
        """Download a matching track from Pixabay and save to output_path.

        Maps the prompt to a genre via GENRE_MAP heuristic, queries the
        Pixabay music API, then downloads the first result's MP3.

        When api_key is empty, writes a 0-byte placeholder without any
        network call — suitable for dry-run and testing.

        Parameters
        ----------
        prompt:
            Text description used to derive the search genre.
        output_path:
            Destination file path for the downloaded MP3.
        duration_seconds:
            Minimum requested duration (used as filter hint; Pixabay may
            return shorter tracks).

        Returns
        -------
        Path
            Path to the downloaded (or placeholder) audio file.

        Raises
        ------
        QuotaExceededError
            On HTTP 429 from Pixabay API.
        RuntimeError
            On HTTP errors or no results found.

        Complexity: O(1) search request + O(file_size) download

        Examples
        --------
        >>> from pathlib import Path
        >>> import tempfile
        >>> adapter = PixabayAudioAdapter(api_key="")
        >>> with tempfile.TemporaryDirectory() as d:
        ...     p = adapter.generate("ambient music", Path(d) / "out.mp3")
        ...     p.exists()
        True
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._api_key:
            logger.debug("PixabayAudioAdapter: no API key — writing placeholder to %s", output_path)
            output_path.write_bytes(b"")
            return output_path

        genre = self._prompt_to_genre(prompt)
        audio_url = self._search(genre)
        self._download(audio_url, output_path)
        logger.info("PixabayAudioAdapter: downloaded %s → %s", genre, output_path)
        return output_path

    def is_available(self) -> bool:
        """Return True if api_key is configured.

        Complexity: O(1)

        Examples
        --------
        >>> PixabayAudioAdapter(api_key="").is_available()
        False
        >>> PixabayAudioAdapter(api_key="abc123").is_available()
        True
        """
        return bool(self._api_key)

    @property
    def service_name(self) -> str:
        """Human-readable service name.

        Examples
        --------
        >>> PixabayAudioAdapter(api_key="").service_name
        'Pixabay Audio'
        """
        return "Pixabay Audio"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _prompt_to_genre(self, prompt: str) -> str:
        """Map a free-text prompt to a Pixabay genre string.

        Checks if any GENRE_MAP key appears in the prompt; falls back to
        'ambient' when no match is found.

        Complexity: O(k) where k = len(GENRE_MAP)

        Examples
        --------
        >>> PixabayAudioAdapter()._prompt_to_genre("ghibli_asmr vibes")
        'ambient'
        """
        prompt_lower = prompt.lower()
        for key, genre in self.GENRE_MAP.items():
            if key in prompt_lower:
                return genre
        return self.GENRE_MAP["generic"]

    def _search(self, genre: str) -> str:
        """Query Pixabay music API and return the audio URL of the first result.

        Parameters
        ----------
        genre:
            Pixabay music genre filter string.

        Returns
        -------
        str
            Direct URL to the MP3 audio file.

        Raises
        ------
        QuotaExceededError
            On HTTP 429.
        RuntimeError
            On other HTTP errors or empty result set.

        Complexity: O(1) single HTTP request
        """
        params = urllib.parse.urlencode(
            {"key": self._api_key, "genre": genre, "per_page": 3}
        )
        url = f"{self.BASE_URL}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "YTAIMBot/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
                body = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise QuotaExceededError("PixabayAudioAdapter: 429 quota exceeded") from exc
            raise RuntimeError(f"PixabayAudioAdapter: HTTP {exc.code} on search") from exc

        hits = body.get("hits", [])
        if not hits:
            raise RuntimeError(f"PixabayAudioAdapter: no results for genre '{genre}'")
        audio_url = hits[0].get("audio", hits[0].get("url", ""))
        if not audio_url:
            raise RuntimeError("PixabayAudioAdapter: result missing audio URL")
        return audio_url

    def _download(self, url: str, output_path: Path) -> None:
        """Download audio from url and write to output_path.

        Complexity: O(file_size)
        """
        req = urllib.request.Request(url, headers={"User-Agent": "YTAIMBot/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:  # nosec B310
                output_path.write_bytes(resp.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"PixabayAudioAdapter: failed to download audio — HTTP {exc.code}"
            ) from exc
