"""Trending character fetcher for Hype niche (Phase P13, T-941).

Maps raw trend keywords to known hype characters and returns ranked
``HypeCharacter`` entities for downstream idea generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from modules.adapters.base import TrendSourceAdapter
from modules.adapters.google_trends import GoogleTrendsTrendSource
from modules.adapters.synthetic import SyntheticTrendSource
from ytaimbot_ml.niches.hype_characters import HypeCharacter, HypeSource
from ytaimbot_ml.utils.text_utils import normalize_keyword

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CharacterAlias:
    """Alias mapping between trend text and canonical character metadata.

    Parameters
    ----------
    alias:
        Text pattern expected in trend keyword stream.
    character_name:
        Canonical display name for video generation.
    franchise:
        Franchise/IP identifier used for SEO and concept grouping.

    Complexity
    ----------
    O(1) data container.
    """

    alias: str
    character_name: str
    franchise: str


class TrendingCharacterFetcher:
    """Fetch and rank trending characters from a trend source.

    Algorithm
    ---------
    1. Fetch trend signals from configured source.
    2. Normalize keywords and match aliases by substring search.
    3. Aggregate per-character best score and source.
    4. Return top-k characters with ``hype_score >= min_hype_score``.

    Complexity
    ----------
    fetch(): O(n * a) where n = number of trend signals, a = number of aliases.

    Examples
    --------
    >>> fetcher = TrendingCharacterFetcher(source=SyntheticTrendSource(seed=42))
    >>> isinstance(fetcher.fetch(), list)
    True
    """

    DEFAULT_ALIASES: tuple[CharacterAlias, ...] = (
        CharacterAlias("judy hopps", "Judy Hopps", "Zootopia 2"),
        CharacterAlias("nick wilde", "Nick Wilde", "Zootopia 2"),
        CharacterAlias("zootopia", "Judy Hopps", "Zootopia 2"),
        CharacterAlias("skibidi", "Skibidi Titan", "Skibidi Universe"),
        CharacterAlias("elsa", "Elsa", "Frozen"),
        CharacterAlias("anna", "Anna", "Frozen"),
        CharacterAlias("spider man", "Spider-Man", "Marvel"),
        CharacterAlias("batman", "Batman", "DC"),
        CharacterAlias("naruto", "Naruto Uzumaki", "Naruto"),
        CharacterAlias("goku", "Goku", "Dragon Ball"),
    )

    def __init__(
        self,
        source: TrendSourceAdapter | None = None,
        min_hype_score: float = 0.7,
        top_k: int = 10,
        aliases: tuple[CharacterAlias, ...] | None = None,
    ) -> None:
        self._source = source or GoogleTrendsTrendSource(geo="US", max_results=50)
        self._fallback = SyntheticTrendSource(seed=42)
        self._min_hype_score = min_hype_score
        self._top_k = top_k
        self._aliases = aliases or self.DEFAULT_ALIASES

    def fetch(self) -> list[HypeCharacter]:
        """Return ranked trending characters with hype score filtering.

        Returns
        -------
        list[HypeCharacter]
            Sorted descending by ``hype_score``; size ``<= top_k``.

        Complexity
        ----------
        O(n * a)

        Examples
        --------
        >>> out = TrendingCharacterFetcher(source=SyntheticTrendSource(seed=1)).fetch()
        >>> isinstance(out, list)
        True
        """
        try:
            signals = self._source.fetch()
        except Exception as exc:  # noqa: BLE001
            logger.warning("TrendingCharacterFetcher: source failed (%s), using fallback", exc)
            signals = self._fallback.fetch()

        aggregated: dict[str, HypeCharacter] = {}
        now = datetime.now(timezone.utc)

        for signal in signals:
            norm = normalize_keyword(signal.keyword)
            for alias in self._aliases:
                if alias.alias not in norm:
                    continue
                char = HypeCharacter(
                    name=alias.character_name,
                    franchise=alias.franchise,
                    hype_score=float(signal.raw_score),
                    source=self._map_source(signal.source),
                    discovered_at=now,
                    keywords=[signal.keyword],
                )
                existing = aggregated.get(char.name)
                if existing is None or char.hype_score > existing.hype_score:
                    aggregated[char.name] = char

        ranked = sorted(
            (
                c
                for c in aggregated.values()
                if c.hype_score >= self._min_hype_score
            ),
            key=lambda x: x.hype_score,
            reverse=True,
        )
        return ranked[: self._top_k]

    @staticmethod
    def _map_source(source: str) -> HypeSource:
        """Map TrendSignal source IDs to HypeSource enum. O(1).

        Examples
        --------
        >>> TrendingCharacterFetcher._map_source("google_trends")
        <HypeSource.GOOGLE_TRENDS: 'google_trends'>
        """
        lowered = source.lower()
        if "google" in lowered:
            return HypeSource.GOOGLE_TRENDS
        if "youtube" in lowered:
            return HypeSource.YOUTUBE_TRENDING
        return HypeSource.MANUAL

