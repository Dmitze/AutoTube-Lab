"""Ghibli ASMR SEO optimizer — Phase P11 (T-910–T-912).

Generates CTR-optimized titles, keyword-rich descriptions, and tag lists
following documented patterns from successful ASMR channels.

Complexity notes
----------------
SeasonalBoost.get_season():     O(1)
SeasonalBoost.get_keywords():   O(1)
GhibliSEO.generate_title():     O(t) where t = number of title templates
GhibliSEO.generate_tags():      O(1)
GhibliSEO.generate_description: O(1)
GhibliSEO.score_title():        O(w) where w = words in title
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field

from ytaimbot_ml.niches.ghibli_asmr import SubNiche

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Title templates: {topic}, {season_kw} are substituted at runtime
# ---------------------------------------------------------------------------

_TITLE_TEMPLATES: list[str] = [
    "Cozy Ghibli ASMR — {topic} 🌿 No Talking, Relaxing Sounds",
    "Ghibli ASMR | {topic} | Relaxing & Cozy | No Talking",
    "Relaxing Ghibli ASMR — {topic} | Cozy Village Sounds",
    "Studio Ghibli ASMR 🌸 {topic} — No Talking, Sleep Aid",
    "Cozy {season_kw} ASMR — {topic} | Ghibli Atmosphere | Relaxing",
    "Ghibli Ambience — {topic} 🍃 ASMR No Talking, Cozy Sounds",
    "ASMR Ghibli Style | {topic} | Cozy & Relaxing No Talking",
    "{topic} — Ghibli ASMR 🌙 Cozy Relaxing No Talking Sounds",
]

_BASE_TAGS: list[str] = [
    "Ghibli ASMR",
    "cozy ASMR",
    "relaxing ASMR",
    "no talking ASMR",
    "Studio Ghibli",
    "ambient sounds",
    "sleep aid",
    "study music",
    "cozy atmosphere",
    "relaxing sounds",
    "Ghibli ambience",
    "cozy animation",
    "no talking",
    "ASMR relaxing",
    "sleep sounds",
]


class SeasonalBoost:
    """Provides season-appropriate keyword boosts for SEO.

    Determines the current season from a date and returns additional
    keywords that boost YouTube algorithm performance during seasonal
    search spikes.

    Complexity: O(1) for all methods

    Examples
    --------
    >>> from datetime import date
    >>> boost = SeasonalBoost()
    >>> keywords = boost.get_keywords(date(2026, 12, 15))
    >>> "cozy winter cabin" in keywords
    True
    >>> boost.get_season(date(2026, 7, 15))
    'summer'
    """

    SEASONAL_KEYWORDS: dict[str, list[str]] = {
        "winter": [
            "cozy winter cabin",
            "snow ASMR",
            "christmas cottage",
            "winter morning Ghibli",
        ],
        "spring": [
            "spring rain",
            "cherry blossom ASMR",
            "cozy spring morning",
            "garden sounds",
        ],
        "summer": [
            "summer cottage",
            "fireflies ASMR",
            "cozy summer night",
            "countryside sounds",
        ],
        "autumn": [
            "autumn leaves ASMR",
            "rainy autumn",
            "harvest season",
            "cozy fall day",
        ],
    }

    def get_season(self, date: datetime.date) -> str:
        """Return the meteorological season for a given date.

        Mapping: Dec–Feb = winter, Mar–May = spring,
                 Jun–Aug = summer, Sep–Nov = autumn.

        Parameters
        ----------
        date:
            Calendar date to evaluate.

        Returns
        -------
        str
            One of "winter", "spring", "summer", "autumn".

        Complexity: O(1)

        Examples
        --------
        >>> SeasonalBoost().get_season(datetime.date(2026, 1, 5))
        'winter'
        >>> SeasonalBoost().get_season(datetime.date(2026, 4, 20))
        'spring'
        """
        month = date.month
        if month in (12, 1, 2):
            return "winter"
        if month in (3, 4, 5):
            return "spring"
        if month in (6, 7, 8):
            return "summer"
        return "autumn"

    def get_keywords(self, date: datetime.date) -> list[str]:
        """Return seasonal keyword boosts for the given date.

        Parameters
        ----------
        date:
            Calendar date used to determine the current season.

        Returns
        -------
        list[str]
            Season-specific keywords (4 items).

        Complexity: O(1)

        Examples
        --------
        >>> kws = SeasonalBoost().get_keywords(datetime.date(2026, 12, 15))
        >>> "cozy winter cabin" in kws
        True
        """
        season = self.get_season(date)
        return list(self.SEASONAL_KEYWORDS[season])


class GhibliSEO:
    """SEO optimizer specifically tuned for Ghibli-style ASMR videos.

    Generates CTR-optimized titles, keyword-rich descriptions, and tag
    lists following documented patterns from successful ASMR channels.

    MUST_HAVE_KEYWORDS always appear in title/tags:
        ``["cozy", "ASMR", "Ghibli", "relaxing", "no talking"]``

    Parameters
    ----------
    sub_niche:
        SubNiche enum value influencing niche-specific tags and titles.
    seasonal_boost:
        Optional SeasonalBoost instance; created automatically if None.

    Complexity
    ----------
    generate_title():       O(t) where t = number of title templates
    generate_tags():        O(1)
    generate_description(): O(1)
    score_title():          O(w) where w = words in title

    Examples
    --------
    >>> seo = GhibliSEO(sub_niche=SubNiche.VILLAGE_LIFE)
    >>> title = seo.generate_title(topic="morning on the hill", season_keywords=["spring rain"])
    >>> len(title) <= 100
    True
    >>> "ASMR" in title or "cozy" in title.lower()
    True
    """

    MUST_HAVE_KEYWORDS: list[str] = ["cozy", "ASMR", "Ghibli", "relaxing", "no talking"]

    def __init__(
        self,
        sub_niche: SubNiche,
        seasonal_boost: SeasonalBoost | None = None,
    ) -> None:
        self._sub_niche = sub_niche
        self._seasonal_boost = seasonal_boost if seasonal_boost is not None else SeasonalBoost()
        logger.debug("GhibliSEO init: sub_niche=%s", sub_niche.value)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_title(
        self,
        topic: str,
        season_keywords: list[str] | None = None,
    ) -> str:
        """Generate a CTR-optimized YouTube title for the given topic.

        Selects the best-scoring template (by ``score_title``) and
        truncates to 100 characters if necessary.

        Parameters
        ----------
        topic:
            Short topic string (e.g. "morning on the hill").
        season_keywords:
            Optional seasonal keyword list; first item used as ``{season_kw}``.

        Returns
        -------
        str
            YouTube title ≤ 100 characters containing ≥ 1 MUST_HAVE keyword.

        Complexity: O(t) where t = number of title templates

        Examples
        --------
        >>> seo = GhibliSEO(SubNiche.VILLAGE_LIFE)
        >>> t = seo.generate_title("cozy morning", ["spring rain"])
        >>> len(t) <= 100
        True
        """
        season_kw = season_keywords[0] if season_keywords else "cozy"
        topic_clean = topic.strip() or "cozy scene"

        candidates = [
            tmpl.format(topic=topic_clean, season_kw=season_kw)
            for tmpl in _TITLE_TEMPLATES
        ]

        scored = [(c, self.score_title(c)) for c in candidates]
        best_title = max(scored, key=lambda x: x[1])[0]

        # Truncate to 100 chars at a word boundary
        if len(best_title) > 100:
            best_title = best_title[:97].rsplit(" ", 1)[0] + "..."

        logger.info("generate_title: topic=%r → %r", topic, best_title)
        return best_title

    def generate_tags(
        self,
        topic: str,
        extra_keywords: list[str] | None = None,
    ) -> list[str]:
        """Generate a YouTube tag list (15–20 tags) for the video.

        Parameters
        ----------
        topic:
            Short topic string to derive topic-specific tags.
        extra_keywords:
            Optional additional tags to append (e.g. seasonal keywords).

        Returns
        -------
        list[str]
            15–20 unique tag strings.

        Complexity: O(1)

        Examples
        --------
        >>> seo = GhibliSEO(SubNiche.VILLAGE_LIFE)
        >>> tags = seo.generate_tags("forest morning")
        >>> len(tags) >= 15
        True
        >>> "Ghibli ASMR" in tags
        True
        """
        tags: list[str] = list(_BASE_TAGS)

        # Add sub-niche specific tag
        niche_tag = self._sub_niche.value.replace("_", " ") + " ASMR"
        tags.append(niche_tag)

        # Add topic-derived tag
        topic_clean = topic.strip()
        if topic_clean:
            tags.append(topic_clean)

        if extra_keywords:
            tags.extend(extra_keywords)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_tags: list[str] = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        logger.debug("generate_tags: topic=%r → %d tags", topic, len(unique_tags))
        return unique_tags

    def generate_description(self, topic: str, scene_count: int = 50) -> str:
        """Generate a 2-paragraph YouTube description for the video.

        Paragraph 1: Atmosphere/mood hook with topic.
        Paragraph 2: SEO-boosted tags section with MUST_HAVE keywords.

        Parameters
        ----------
        topic:
            Short topic string.
        scene_count:
            Number of scenes in the video.

        Returns
        -------
        str
            Two-paragraph description suitable for YouTube upload.

        Complexity: O(1)

        Examples
        --------
        >>> seo = GhibliSEO(SubNiche.VILLAGE_LIFE)
        >>> desc = seo.generate_description("morning in the village")
        >>> "Ghibli" in desc and "ASMR" in desc
        True
        >>> len(desc) > 100
        True
        """
        niche_label = self._sub_niche.value.replace("_", " ")
        para1 = (
            f"✨ Welcome to a cozy Ghibli-style ASMR journey — {topic}. "
            f"This {scene_count}-scene video captures the peaceful {niche_label} atmosphere "
            f"with soft ambient sounds, gentle visuals, and no talking. "
            f"Perfect for relaxing, studying, or falling asleep."
        )
        must_have_str = " | ".join(self.MUST_HAVE_KEYWORDS)
        para2 = (
            f"🎐 {must_have_str}\n"
            f"Tags: Ghibli ASMR, {niche_label} ASMR, relaxing animation, cozy sounds, "
            f"no talking ASMR, sleep sounds, Studio Ghibli ambience, {topic}"
        )
        return f"{para1}\n\n{para2}"

    def score_title(self, title: str) -> float:
        """Score a title for CTR potential using MUST_HAVE keyword coverage.

        Score formula (all components in [0, 1]):
            0.60 × keyword_coverage   (fraction of MUST_HAVE keywords present)
            0.25 × length_ok          (1.0 if 40 ≤ len ≤ 100 chars)
            0.15 × has_emoji          (1.0 if title contains an emoji)

        Parameters
        ----------
        title:
            Candidate title string.

        Returns
        -------
        float
            Composite CTR score in [0, 1].

        Complexity: O(w) where w = words in title

        Examples
        --------
        >>> seo = GhibliSEO(SubNiche.VILLAGE_LIFE)
        >>> s = seo.score_title("Cozy Ghibli ASMR — relaxing no talking village")
        >>> 0.0 <= s <= 1.0
        True
        """
        title_lower = title.lower()

        # Keyword coverage: fraction of MUST_HAVE present
        hits = sum(1 for kw in self.MUST_HAVE_KEYWORDS if kw.lower() in title_lower)
        keyword_coverage = hits / len(self.MUST_HAVE_KEYWORDS)

        # Length score
        length = len(title)
        if 40 <= length <= 100:
            length_ok = 1.0
        elif length < 40:
            length_ok = length / 40.0
        else:
            over = length - 100
            length_ok = max(0.0, 1.0 - over / 50.0)

        # Emoji presence boosts visual CTR
        has_emoji = 1.0 if any(ord(ch) > 127 for ch in title) else 0.0

        score = 0.60 * keyword_coverage + 0.25 * length_ok + 0.15 * has_emoji
        return round(score, 4)
