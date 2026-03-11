"""Ghibli-style ASMR niche profile — Phase P11 (T-900–T-903).

Defines the content strategy profile that drives all downstream stages:
image prompt construction, script generation, and SEO metadata.

Complexity notes
----------------
GhibliASMRProfile:    O(1) — pure data container
scene_prompt_prefix:  O(k) where k = number of style_tags
llm_system_prompt:    O(1)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SubNiche(str, Enum):
    """Enumeration of Ghibli ASMR sub-niche categories.

    Each value maps to a distinct visual/emotional theme used in
    prompt construction and SEO metadata.

    Examples
    --------
    >>> SubNiche.VILLAGE_LIFE.value
    'village_life'
    >>> SubNiche("winter_cozy")
    <SubNiche.WINTER_COZY: 'winter_cozy'>
    """

    WINTER_COZY = "winter_cozy"
    CHILDHOOD_NOSTALGIA = "childhood_nostalgia"
    ELDERLY_LIFE = "elderly_life"
    VILLAGE_LIFE = "village_life"
    UNUSUAL_PLACES = "unusual_places"
    NATURE_RAIN = "nature_rain"


@dataclass
class GhibliASMRProfile:
    """Content strategy profile for the Ghibli-style ASMR niche.

    Defines video structure rules, required style constraints, and
    LLM prompt templates for generating 50-scene ASMR videos.

    Parameters
    ----------
    sub_niche:
        Target sub-niche category (default: VILLAGE_LIFE).
    scenes_per_video:
        Number of image scenes in one video (default: 50).
    seconds_per_scene:
        Duration of each scene in seconds (default: 7).
    language:
        Output language ISO code for generated scripts (default: "en").
    style_tags:
        Visual style tags injected into every Imagen/LLM prompt.

    Complexity
    ----------
    O(1) — pure data container

    Examples
    --------
    >>> profile = GhibliASMRProfile(sub_niche=SubNiche.VILLAGE_LIFE)
    >>> profile.scenes_per_video
    50
    >>> profile.seconds_per_scene
    7
    >>> profile.duration_seconds
    350
    """

    sub_niche: SubNiche = SubNiche.VILLAGE_LIFE
    scenes_per_video: int = 50
    seconds_per_scene: int = 7
    language: str = "en"
    style_tags: list[str] = field(
        default_factory=lambda: [
            "Studio Ghibli style",
            "soft watercolor",
            "warm lighting",
            "cozy atmosphere",
            "no text",
            "2D animation style",
        ]
    )

    @property
    def duration_seconds(self) -> int:
        """Total video duration in seconds.

        Complexity: O(1)

        Examples
        --------
        >>> GhibliASMRProfile(scenes_per_video=50, seconds_per_scene=7).duration_seconds
        350
        """
        return self.scenes_per_video * self.seconds_per_scene

    @property
    def duration_minutes(self) -> float:
        """Total video duration in minutes.

        Complexity: O(1)

        Examples
        --------
        >>> round(GhibliASMRProfile().duration_minutes, 2)
        5.83
        """
        return self.duration_seconds / 60

    def scene_prompt_prefix(self) -> str:
        """Return the style prefix for Imagen/LLM scene prompts.

        Joins all style_tags with commas and appends the sub-niche name.

        Complexity: O(k) where k = number of style_tags

        Returns
        -------
        str
            Comma-separated style tags followed by the sub-niche label.

        Examples
        --------
        >>> profile = GhibliASMRProfile(sub_niche=SubNiche.WINTER_COZY)
        >>> "Studio Ghibli style" in profile.scene_prompt_prefix()
        True
        >>> "winter cozy" in profile.scene_prompt_prefix()
        True
        """
        tags = ", ".join(self.style_tags)
        niche_label = self.sub_niche.value.replace("_", " ")
        logger.debug("scene_prompt_prefix: niche=%s tags=%d", self.sub_niche.value, len(self.style_tags))
        return f"{tags}, {niche_label} setting"

    def llm_system_prompt(self) -> str:
        """Return the ChatGPT/Groq system prompt for script generation.

        Complexity: O(1)

        Returns
        -------
        str
            System prompt instructing the LLM to produce scene descriptions.

        Examples
        --------
        >>> profile = GhibliASMRProfile()
        >>> prompt = profile.llm_system_prompt()
        >>> "50" in prompt and "Ghibli" in prompt
        True
        """
        logger.debug("llm_system_prompt: sub_niche=%s", self.sub_niche.value)
        return (
            f"You are a Ghibli-style ASMR video creator. "
            f"Generate {self.scenes_per_video} short scene descriptions "
            f"(each ~{self.seconds_per_scene} seconds) for a cozy '{self.sub_niche.value}' video. "
            f"Each scene should: evoke nostalgia/peace, describe visual + ambient sounds, "
            f"feature consistent characters if any. Output in English. No dialogue text."
        )
