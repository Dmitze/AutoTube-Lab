"""PexelsStockAdapter: free stock video search and download via Pexels + Pixabay APIs.

Free tiers (2026):
  Pexels  : free API key, 200 req/hour, 20 000 req/month, commercial use ✅
  Pixabay : free API key, 100 req/min, 5 000 req/day, commercial use ✅
  License : both allow commercial use without attribution on free tier

Environment variables:
  PEXELS_API_KEY   : from pexels.com/api (free signup)
  PIXABAY_API_KEY  : from pixabay.com/api/docs (free signup)
  PEXELS_PER_PAGE  : results per search (default 10, max 80)

Algorithm — Best-First Selection:
  search() → filter by duration → sort by resolution desc → take top-N
  Complexity: O(k log k) where k = results per page
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_PEXELS_URL = "https://api.pexels.com/videos/search"
_PIXABAY_URL = "https://pixabay.com/api/videos/"


@dataclass
class StockVideo:
    """Metadata for one stock video clip.

    Examples
    --------
    >>> v = StockVideo(id="1", url="https://x.mp4", preview_url="", width=1920, height=1080, duration=10, provider="pexels")
    >>> v.is_hd
    True
    """

    id: str
    url: str
    preview_url: str
    width: int
    height: int
    duration: int       # seconds
    provider: str       # "pexels" | "pixabay"
    keywords: list[str] = field(default_factory=list)

    @property
    def is_hd(self) -> bool:
        """True if width >= 1280 (720p or better)."""
        return self.width >= 1280


class PexelsStockAdapter:
    """Search + download free stock videos (Pexels primary, Pixabay fallback).

    Both services are completely free for commercial use.
    No watermarks, no attribution required.

    Parameters
    ----------
    pexels_key:
        Pexels API key. Defaults to ``PEXELS_API_KEY`` env var.
    pixabay_key:
        Pixabay API key. Defaults to ``PIXABAY_API_KEY`` env var.
    output_dir:
        Download directory. Default: ``data/stock``.

    Complexity
    ----------
    search():   O(k log k) — sort k results
    download(): O(file_size) — streamed HTTP

    Examples
    --------
    >>> adapter = PexelsStockAdapter(pexels_key="fake")
    >>> isinstance(adapter.fetch_for_plan([]), list)
    True
    """

    def __init__(
        self,
        pexels_key: str | None = None,
        pixabay_key: str | None = None,
        output_dir: str | Path = "data/stock",
    ) -> None:
        self._pexels_key = pexels_key or os.environ.get("PEXELS_API_KEY", "")
        self._pixabay_key = pixabay_key or os.environ.get("PIXABAY_API_KEY", "")
        self._output_dir = Path(output_dir)
        self._client = httpx.Client(timeout=60.0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        keywords: list[str],
        min_duration: int = 5,
        max_duration: int = 60,
        orientation: str = "landscape",
        count: int = 5,
    ) -> list[StockVideo]:
        """Search for free stock videos matching keywords.

        Tries Pexels first; if fewer than count results, adds Pixabay results.
        Returns sorted by resolution (best first).

        Parameters
        ----------
        keywords:
            Search terms joined as a single query.
        min_duration / max_duration:
            Clip length filter in seconds.
        orientation:
            ``"landscape"`` | ``"portrait"`` | ``"square"``.
        count:
            Max results to return.

        Returns
        -------
        list[StockVideo]
            HD-first sorted list. Empty if no API keys configured.

        Complexity: O(k log k)

        Examples
        --------
        >>> PexelsStockAdapter().search([])
        []
        """
        if not keywords:
            return []

        query = " ".join(keywords[:5])  # limit query length
        results: list[StockVideo] = []

        if self._pexels_key:
            results.extend(
                self._search_pexels(query, min_duration, max_duration, orientation)
            )

        if len(results) < count and self._pixabay_key:
            results.extend(
                self._search_pixabay(query, min_duration, max_duration)
            )

        results.sort(key=lambda v: v.width * v.height, reverse=True)
        return results[:count]

    def download(self, video: StockVideo, filename: str | None = None) -> Path:
        """Download a StockVideo MP4 to disk (cached — won't re-download).

        Parameters
        ----------
        video:
            StockVideo with valid ``url``.
        filename:
            Override file stem. Defaults to video ID.

        Returns
        -------
        Path
            Path to the downloaded MP4.

        Complexity: O(file_size)

        Examples
        --------
        >>> # Requires real StockVideo.url
        >>> PexelsStockAdapter.__name__
        'PexelsStockAdapter'
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)
        stem = re.sub(r"[^\w\-]", "_", filename or f"{video.provider}_{video.id}")
        out = self._output_dir / f"{stem}.mp4"

        if out.exists():
            logger.debug("Cached: %s", out)
            return out

        logger.info("Downloading stock %s/%s → %s", video.provider, video.id, out)
        with self._client.stream("GET", video.url) as resp:
            resp.raise_for_status()
            with open(out, "wb") as fh:
                for chunk in resp.iter_bytes(65536):
                    fh.write(chunk)
        return out

    def fetch_for_plan(
        self,
        keywords: list[str],
        count: int = 5,
        max_duration: int = 30,
    ) -> list[Path]:
        """Search + download stock clips matching a content plan's keywords.

        Parameters
        ----------
        keywords:
            From ContentPlan.keywords.
        count:
            Number of clips to download.
        max_duration:
            Max clip length in seconds.

        Returns
        -------
        list[Path]
            Downloaded MP4 paths. Empty list if no API keys set (graceful).

        Complexity: O(count × file_size)

        Examples
        --------
        >>> PexelsStockAdapter().fetch_for_plan(["python"])
        []
        """
        if not self._pexels_key and not self._pixabay_key:
            logger.info("PexelsStockAdapter: no API keys — stock footage skipped")
            return []

        videos = self.search(keywords, max_duration=max_duration, count=count)
        paths: list[Path] = []
        for v in videos:
            try:
                paths.append(self.download(v))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Stock download failed %s/%s: %s", v.provider, v.id, exc)
        return paths

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _search_pexels(
        self,
        query: str,
        min_dur: int,
        max_dur: int,
        orientation: str,
    ) -> list[StockVideo]:
        """Query Pexels Videos API. Complexity: O(per_page)."""
        per_page = int(os.environ.get("PEXELS_PER_PAGE", "10"))
        try:
            resp = self._client.get(
                _PEXELS_URL,
                params={
                    "query": query,
                    "per_page": per_page,
                    "orientation": orientation,
                    "min_duration": min_dur,
                    "max_duration": max_dur,
                },
                headers={"Authorization": self._pexels_key},
            )
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Pexels search error: %s", exc)
            return []

        out: list[StockVideo] = []
        for v in resp.json().get("videos", []):
            files = sorted(
                v.get("video_files", []),
                key=lambda f: f.get("width", 0),
                reverse=True,
            )
            best = files[0] if files else None
            if best and best.get("link"):
                out.append(StockVideo(
                    id=str(v["id"]),
                    url=best["link"],
                    preview_url=v.get("image", ""),
                    width=best.get("width", 0),
                    height=best.get("height", 0),
                    duration=v.get("duration", 0),
                    provider="pexels",
                    keywords=query.split(),
                ))
        return out

    def _search_pixabay(
        self,
        query: str,
        min_dur: int,
        max_dur: int,
    ) -> list[StockVideo]:
        """Query Pixabay Videos API. Complexity: O(per_page)."""
        try:
            resp = self._client.get(
                _PIXABAY_URL,
                params={"key": self._pixabay_key, "q": query, "per_page": 10},
            )
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Pixabay search error: %s", exc)
            return []

        out: list[StockVideo] = []
        for hit in resp.json().get("hits", []):
            dur = hit.get("duration", 0)
            if not (min_dur <= dur <= max_dur):
                continue
            vids = hit.get("videos", {})
            best = vids.get("large") or vids.get("medium") or vids.get("small") or {}
            if best.get("url"):
                out.append(StockVideo(
                    id=str(hit["id"]),
                    url=best["url"],
                    preview_url=hit.get("userImageURL", ""),
                    width=best.get("width", 0),
                    height=best.get("height", 0),
                    duration=dur,
                    provider="pixabay",
                    keywords=query.split(),
                ))
        return out
