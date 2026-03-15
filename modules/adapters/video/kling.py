"""KlingAdapter: optional Kling AI video generation (Phase P13, T-948).

This adapter is optional because Kling is a paid external service.
Default behavior is safe for local/tests: when not configured it writes a
placeholder output file without performing network calls.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.klingai.com/v1"


class KlingAdapter:
    """Generate short video clips from text prompts using Kling API.

    Parameters
    ----------
    api_key:
        Kling API key. Defaults to ``KLING_API_KEY`` environment variable.
    enabled:
        Explicit feature toggle. Defaults to ``KLING_ENABLED`` env (false).
    max_poll_attempts:
        Maximum polling iterations for async generation status.
    poll_interval_seconds:
        Wait time between polls.

    Complexity
    ----------
    ``generate()``: O(p) where p is the number of poll attempts.

    Examples
    --------
    >>> adapter = KlingAdapter(api_key="", enabled=False)
    >>> adapter.is_available()
    False
    """

    def __init__(
        self,
        api_key: str = "",
        enabled: bool | None = None,
        max_poll_attempts: int = 30,
        poll_interval_seconds: float = 2.0,
    ) -> None:
        env_enabled = os.environ.get("KLING_ENABLED", "false").lower() == "true"
        self._api_key = api_key or os.environ.get("KLING_API_KEY", "")
        self._enabled = env_enabled if enabled is None else enabled
        self._max_poll_attempts = max_poll_attempts
        self._poll_interval_seconds = poll_interval_seconds

    def is_available(self) -> bool:
        """Return True when adapter is enabled and key is configured. O(1).

        Examples
        --------
        >>> KlingAdapter(api_key="", enabled=True).is_available()
        False
        """
        return self._enabled and bool(self._api_key)

    @property
    def service_name(self) -> str:
        """Human-readable service name. O(1)."""
        return "Kling AI"

    def generate(
        self,
        prompt: str,
        output_path: Path,
        duration_seconds: int = 8,
    ) -> Path:
        """Generate a video clip from prompt and save to ``output_path``.

        When adapter is unavailable (disabled/no key), writes a placeholder file
        and returns immediately so pipeline remains fail-safe.

        Parameters
        ----------
        prompt:
            Text prompt describing desired visual animation.
        output_path:
            Destination file path for resulting MP4.
        duration_seconds:
            Target clip duration in seconds.

        Returns
        -------
        Path
            Output file path.

        Complexity
        ----------
        O(p) polling + O(file_size) download.

        Examples
        --------
        >>> import tempfile
        >>> from pathlib import Path
        >>> with tempfile.TemporaryDirectory() as d:
        ...     out = KlingAdapter(api_key="", enabled=False).generate("cat", Path(d) / "x.mp4")
        ...     out.exists()
        True
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.is_available():
            logger.debug("KlingAdapter unavailable; writing placeholder to %s", output_path)
            output_path.write_bytes(b"")
            return output_path

        job_id = self._submit_generation(prompt, duration_seconds)
        video_url = self._poll_until_complete(job_id)
        self._download(video_url, output_path)
        return output_path

    def _submit_generation(self, prompt: str, duration_seconds: int) -> str:
        """POST generation request and return job ID. O(1).

        Raises
        ------
        RuntimeError
            On HTTP or response-shape failures.
        """
        req = urllib.request.Request(
            f"{_BASE_URL}/videos/generate",
            data=json.dumps(
                {"prompt": prompt, "duration_seconds": duration_seconds}
            ).encode(),
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
            raise RuntimeError(f"KlingAdapter submit failed: HTTP {exc.code}") from exc

        job_id = body.get("job_id", "")
        if not job_id:
            raise RuntimeError("KlingAdapter submit failed: missing job_id")
        return str(job_id)

    def _poll_until_complete(self, job_id: str) -> str:
        """Poll job status endpoint until completion and return video URL. O(p)."""
        req = urllib.request.Request(
            f"{_BASE_URL}/videos/{job_id}",
            headers={"Authorization": f"Bearer {self._api_key}"},
            method="GET",
        )

        for _ in range(self._max_poll_attempts):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
                    body = json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f"KlingAdapter poll failed: HTTP {exc.code}") from exc

            status = str(body.get("status", "")).lower()
            if status == "completed":
                video_url = str(body.get("video_url", ""))
                if not video_url:
                    raise RuntimeError("KlingAdapter poll failed: missing video_url")
                return video_url
            if status == "failed":
                raise RuntimeError(f"KlingAdapter generation failed: {body.get('error', 'unknown')}")
            time.sleep(self._poll_interval_seconds)

        raise RuntimeError("KlingAdapter polling timed out")

    @staticmethod
    def _download(video_url: str, output_path: Path) -> None:
        """Download MP4 from ``video_url`` into ``output_path``. O(file_size)."""
        with urllib.request.urlopen(video_url, timeout=60) as resp:  # nosec B310
            output_path.write_bytes(resp.read())

