"""AI Stories niche — narrated story videos with AI voice + AI images.

Strategy:
- Find viral story ideas (horror, drama, mystery) with 800k+ views
- Generate script via Groq LLM
- AI voice narration (ElevenLabs → edge-tts chain)
- AI images as visual backdrop
- RPM $2–5, monetization in 3–4 weeks
- Target: global EN audience, age 18–35

Complexity notes
----------------
AIStoriesProfile.get_llm_prompt:  O(1)
AIStoriesProfile.get_seo_title:   O(1)
AIStoriesProfile.get_seo_tags:    O(1)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger(__name__)


class StoryGenre(str, Enum):
    """Genre of the AI-narrated story.

    Examples
    --------
    >>> StoryGenre.HORROR.value
    'horror'
    """

    HORROR = "horror"
    DRAMA = "drama"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    MOTIVATION = "motivation"
    HISTORICAL = "historical"


@dataclass
class AIStoriesProfile:
    """Content strategy profile for AI Stories niche.

    Narrated story videos: AI script → AI voice → AI images → assembled video.
    No face cam, no manual recording. Fully automatable.

    Parameters
    ----------
    genre:
        Story genre determining tone and SEO tags.
    target_duration_minutes:
        Target video length in minutes (default 10 = max ad breaks).
    target_word_count:
        Approximate script word count (~150 wpm for 10 min).
    language:
        BCP-47 language code for narration and tags.
    rpm_estimate_usd:
        Expected RPM in USD (default $3.5, range $2–5).

    Complexity: O(1) for all methods

    Examples
    --------
    >>> profile = AIStoriesProfile(genre=StoryGenre.HORROR)
    >>> profile.target_duration_minutes
    10
    >>> profile.rpm_estimate_usd
    3.5
    """

    genre: StoryGenre = StoryGenre.DRAMA
    target_duration_minutes: int = 10       # 10 min = max ad breaks
    target_word_count: int = 1500           # ~10 min at 150 wpm
    language: str = "en"
    rpm_estimate_usd: float = 3.5           # $2–5 average

    # Story must have these structural elements for high retention
    STORY_STRUCTURE: list[str] = field(default_factory=lambda: [
        "hook_30s",         # shocking first line — grab viewer instantly
        "setup_2min",       # establish characters and world
        "conflict_3min",    # problem escalates (tension build)
        "twist_2min",       # unexpected revelation
        "climax_2min",      # peak emotion/action
        "resolution_1min",  # satisfying ending with moral
    ])

    AI_DISCLAIMER: str = (
        "⚠️ This is a fictional AI-generated story. "
        "All events, characters, and places are entirely made up. "
        "Created with AI: script, voice, and visuals. "
        "Not intended as factual reporting. For entertainment only."
    )

    def get_llm_prompt(self, topic: str) -> str:
        """Build a Groq LLM prompt for generating a story script.

        Parameters
        ----------
        topic:
            Story topic or premise (e.g. "abandoned lighthouse keeper").

        Returns
        -------
        str
            Ready-to-use LLM prompt string.

        Complexity: O(1)

        Examples
        --------
        >>> profile = AIStoriesProfile(genre=StoryGenre.HORROR)
        >>> prompt = profile.get_llm_prompt("haunted lighthouse")
        >>> "horror" in prompt
        True
        >>> "1500" in prompt
        True
        """
        return (
            f"Write a {self.genre.value} story for a YouTube narration video. "
            f"Topic: {topic}. "
            f"Length: approximately {self.target_word_count} words. "
            f"Structure: hook (30s) → setup → conflict → twist → climax → resolution. "
            f"Style: engaging narration, second-person perspective ('You wake up and...'), "
            f"present tense, vivid sensory details, emotional moments. "
            f"End with a moral lesson. No dialogue tags. Pure narration."
        )

    def get_seo_title(self, topic: str) -> str:
        """Generate a CTR-optimized title for a story video.

        Parameters
        ----------
        topic:
            Story topic phrase.

        Returns
        -------
        str
            YouTube title ≤ 100 characters.

        Complexity: O(1)

        Examples
        --------
        >>> profile = AIStoriesProfile(genre=StoryGenre.HORROR)
        >>> title = profile.get_seo_title("abandoned lighthouse")
        >>> len(title) <= 100
        True
        >>> "abandoned lighthouse" in title
        True
        """
        prefix_by_genre: dict[StoryGenre, str] = {
            StoryGenre.HORROR:     "I Woke Up And...",
            StoryGenre.DRAMA:      "Nobody Believed Me When I Said...",
            StoryGenre.MYSTERY:    "The Truth About",
            StoryGenre.ROMANCE:    "She Left Without Saying",
            StoryGenre.MOTIVATION: "From Zero to Everything:",
            StoryGenre.HISTORICAL: "The Untold Story of",
        }
        prefix = prefix_by_genre.get(self.genre, "The Story of")
        return f"{prefix} {topic}"[:100]

    def get_seo_tags(self, topic: str) -> list[str]:
        """Generate 15–20 SEO tags for the story video.

        Parameters
        ----------
        topic:
            Story topic used as an additional tag.

        Returns
        -------
        list[str]
            15–20 SEO tag strings.

        Complexity: O(1)

        Examples
        --------
        >>> profile = AIStoriesProfile(genre=StoryGenre.HORROR)
        >>> tags = profile.get_seo_tags("haunted house")
        >>> len(tags) >= 15
        True
        >>> "haunted house" in tags
        True
        """
        genre_tags: dict[StoryGenre, list[str]] = {
            StoryGenre.HORROR:     ["horror story", "scary story", "creepy", "horror narration"],
            StoryGenre.DRAMA:      ["drama story", "emotional story", "sad story", "true drama"],
            StoryGenre.MYSTERY:    ["mystery story", "unsolved mystery", "thriller story"],
            StoryGenre.ROMANCE:    ["love story", "romantic story", "emotional love"],
            StoryGenre.MOTIVATION: ["motivational story", "success story", "inspiring"],
            StoryGenre.HISTORICAL: ["history story", "historical", "untold history"],
        }
        base: list[str] = [
            "AI story",
            "narrated story",
            "story time",
            "AI voice",
            topic,
            "AI generated story",
            "audio story",
            "short story",
            "AI narration",
            "fictional story",
            "story video",
            "voice narration",
        ]
        specific = genre_tags.get(self.genre, [])
        return (base + specific)[:20]
