"""Hype Characters niche — trending animated characters (Zootopia, Skibidi, etc.)

Strategy (proven: $20k/month in 2 months):
- Find trending characters from "D-Second" channel or YouTube trending
- Copy successful story ideas from other niches, replace with trending characters
- RPM $1.5–2 but millions of views → $3k–$10k/month
- Monetization in as little as 2 weeks
- Target audience: children/teens (global EN)

Complexity notes
----------------
HypeCharacter.is_hot:                O(1)
HypeVideoIdea.expected_views_estimate: O(1)
HypeCharactersProfile.get_seo_title:   O(1)
HypeCharactersProfile.get_seo_tags:    O(1)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

log = logging.getLogger(__name__)


class HypeSource(str, Enum):
    """Where to discover trending characters.

    Examples
    --------
    >>> HypeSource.D_SECOND_CHANNEL.value
    'd_second_channel'
    """

    D_SECOND_CHANNEL = "d_second_channel"   # YouTube channel that tracks hypes
    YOUTUBE_TRENDING = "youtube_trending"   # YouTube trending page
    GOOGLE_TRENDS = "google_trends"         # Google Trends spike
    MANUAL = "manual"                       # manually specified


@dataclass
class HypeCharacter:
    """A trending character/IP to build a YouTube channel around.

    Parameters
    ----------
    name:
        Character's display name (e.g. "Judy Hopps").
    franchise:
        Franchise or IP the character belongs to (e.g. "Zootopia 2").
    hype_score:
        Trend intensity in [0.0, 1.0] derived from trend data.
    source:
        Data source where the trend was detected.
    discovered_at:
        UTC timestamp of discovery; defaults to now.
    keywords:
        Optional SEO keywords associated with the character.

    Complexity: O(1) — data container

    Examples
    --------
    >>> c = HypeCharacter(name="Judy Hopps", franchise="Zootopia 2",
    ...                   hype_score=0.95, source=HypeSource.YOUTUBE_TRENDING)
    >>> c.is_hot
    True
    >>> c.hype_score >= 0.7
    True
    """

    name: str
    franchise: str
    hype_score: float
    source: HypeSource
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    keywords: list[str] = field(default_factory=list)

    @property
    def is_hot(self) -> bool:
        """True if hype_score >= 0.7. O(1).

        Examples
        --------
        >>> HypeCharacter("Nick Wilde", "Zootopia 2", 0.9, HypeSource.MANUAL).is_hot
        True
        >>> HypeCharacter("Nick Wilde", "Zootopia 2", 0.5, HypeSource.MANUAL).is_hot
        False
        """
        return self.hype_score >= 0.7


@dataclass
class HypeVideoIdea:
    """A video idea for a hype character based on proven story templates.

    Strategy: take high-view story from ANY niche, replace characters
    with trending ones. Documented to produce 1.6M–2.9M views.

    Parameters
    ----------
    character:
        The trending HypeCharacter to feature.
    story_template:
        One of the PROVEN_STORY_TEMPLATES keys.
    original_views:
        View count of the source video being adapted.
    title:
        Generated SEO title (optional; fill after calling get_seo_title).
    duration_target_seconds:
        Target video length in seconds (default 480 = 8 min for ad breaks).

    Complexity: O(1)

    Examples
    --------
    >>> idea = HypeVideoIdea(
    ...     character=HypeCharacter("Nick Wilde", "Zootopia 2", 0.9, HypeSource.MANUAL),
    ...     story_template="betrayal_drama",
    ...     original_views=3_000_000,
    ... )
    >>> idea.expected_views_estimate > 0
    True
    >>> idea.expected_views_estimate
    1500000
    """

    character: HypeCharacter
    story_template: str
    original_views: int
    title: str = ""
    duration_target_seconds: int = 480  # 8 min = more ad breaks

    @property
    def expected_views_estimate(self) -> int:
        """Conservative estimate: 50% of original_views. O(1).

        Examples
        --------
        >>> idea = HypeVideoIdea(
        ...     HypeCharacter("A", "B", 0.8, HypeSource.MANUAL),
        ...     "betrayal_drama", 2_000_000,
        ... )
        >>> idea.expected_views_estimate
        1000000
        """
        return int(self.original_views * 0.5)


class HypeCharactersProfile:
    """Content strategy for Hype Characters niche.

    Based on proven results: $20k/month using Zootopia 2 characters
    with AI-generated animations, music, and scripts.

    Key rules:
    1. Find trending character (hype_score >= 0.7)
    2. Find proven story template (3M+ views in any niche)
    3. Replace characters, keep story structure
    4. 8+ minutes for max ad revenue
    5. Dramatic/emotional thumbnail (shock, tears, betrayal)

    Complexity: O(1) for all methods

    Examples
    --------
    >>> profile = HypeCharactersProfile()
    >>> profile.min_video_duration_seconds
    480
    >>> "betrayal" in profile.best_story_templates[0]
    True
    """

    min_video_duration_seconds: int = 480   # 8 min
    target_rpm_usd: float = 1.75            # avg $1.5–2
    target_ctr_pct: float = 10.0            # aim for 10% (above average)
    language: str = "en"

    PROVEN_STORY_TEMPLATES: list[str] = [
        "betrayal_drama",            # husband betrays wife → viral
        "unexpected_hero",           # weak character saves everyone
        "family_reunion_tears",      # separated family reunites
        "jealousy_revenge",          # jealous character gets karma
        "forbidden_love",            # two characters from rival groups
        "rags_to_riches",            # poor character becomes powerful
        "sacrifice_for_love",        # character sacrifices everything
    ]

    THUMBNAIL_TRIGGERS: list[str] = [
        "shocked_face",      # big eyes, mouth open
        "tears",             # crying character
        "betrayal_look",     # suspicious sideways glance
        "red_arrows",        # pointing at dramatic element
        "villain_closeup",   # antagonist face large
        "dramatic_contrast", # good vs evil side by side
    ]

    AI_DISCLAIMER: str = (
        "🤖 AI-Generated Animation | All characters belong to their respective owners. "
        "This is fan-made fictional content for entertainment only. "
        "All characters depicted are adults (18+). "
        "Created with AI tools (image generation + animation + music)."
    )

    @property
    def best_story_templates(self) -> list[str]:
        """Return PROVEN_STORY_TEMPLATES (alias for test convenience). O(1).

        Examples
        --------
        >>> HypeCharactersProfile().best_story_templates[0]
        'betrayal_drama'
        """
        return self.PROVEN_STORY_TEMPLATES

    def get_seo_title(self, character_name: str, template: str) -> str:
        """Generate a CTR-optimized title for a hype character video.

        Parameters
        ----------
        character_name:
            Display name of the trending character.
        template:
            Story template key from PROVEN_STORY_TEMPLATES.

        Returns
        -------
        str
            YouTube title ≤ 100 characters.

        Complexity: O(1)

        Examples
        --------
        >>> p = HypeCharactersProfile()
        >>> title = p.get_seo_title("Judy Hopps", "betrayal_drama")
        >>> len(title) <= 100
        True
        >>> "Judy Hopps" in title
        True
        """
        templates: dict[str, str] = {
            "betrayal_drama":       f"{character_name} Was BETRAYED... 😭 (Sad Story)",
            "unexpected_hero":      f"Nobody Believed {character_name}... Until This Happened 😮",
            "family_reunion_tears": f"{character_name} Finally Found Their Family 😢💔",
            "jealousy_revenge":     f"They Were Jealous of {character_name}... Big Mistake 😤",
            "forbidden_love":       f"{character_name}'s Secret Love Story 💔 (Sad Ending)",
            "rags_to_riches":       f"From Nobody to Legend — {character_name}'s Story 🔥",
            "sacrifice_for_love":   f"{character_name} Gave Up Everything For Love 😭",
        }
        title = templates.get(template, f"{character_name} — Sad Story 😭")
        return title[:100]

    def get_seo_tags(self, character_name: str, franchise: str) -> list[str]:
        """Generate 15–20 SEO tags for a hype character video.

        Parameters
        ----------
        character_name:
            Display name of the trending character.
        franchise:
            Franchise or IP name.

        Returns
        -------
        list[str]
            15–20 SEO tag strings.

        Complexity: O(1)

        Examples
        --------
        >>> p = HypeCharactersProfile()
        >>> tags = p.get_seo_tags("Judy Hopps", "Zootopia 2")
        >>> len(tags) >= 15
        True
        >>> "Judy Hopps" in tags
        True
        """
        base: list[str] = [
            character_name,
            franchise,
            f"{character_name} sad story",
            f"{franchise} animation",
            f"{character_name} AI animation",
            "AI cartoon",
            "animated story",
            "sad cartoon",
            "emotional story",
            "AI generated animation",
            "cartoon drama",
            f"{franchise} fan made",
            "AI music video",
            "animated music",
            "cartoon 2026",
        ]
        return base[:20]
