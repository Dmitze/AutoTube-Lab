"""Story script generator for AI Stories niche (Phase P13, T-945).

Generates a 6-act long-form narration script (~1500 words) using an LLM adapter
and returns the canonical ``Script`` / ``ScriptSection`` schemas.

Algorithm
---------
1. Build section prompts from ``AIStoriesProfile`` + topic.
2. Call LLM once per section.
3. Deterministically inject keywords via seeded RNG.
4. Validate total script size.

Complexity
----------
generate(): O(s * (p + t)) where s=6 sections, p=prompt size, t=generated text size.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import numpy as np

from ytaimbot_ml.niches.ai_stories import AIStoriesProfile
from ytaimbot_ml.schemas import Script, ScriptSection

if TYPE_CHECKING:
    from modules.adapters.base import LLMAdapter

logger = logging.getLogger(__name__)

_MIN_SECTION_WORDS = 80


class StoryScriptGenerator:
    """Generates structured AI Stories scripts with a 6-act retention format.

    Parameters
    ----------
    llm:
        LLM adapter implementing ``generate(prompt, max_tokens)``.
    language:
        ISO language code used in prompts. Default is ``"en"``.
    target_word_count:
        Target full script size. Default is 1500 words.
    min_completion_ratio:
        Minimum acceptable generated size ratio relative to ``target_word_count``.
        Example: 0.7 means 70% minimum.

    Complexity
    ----------
    ``generate()``: O(s * (p + t))

    Examples
    --------
    >>> from unittest.mock import MagicMock
    >>> llm = MagicMock()
    >>> llm.generate.return_value = "word " * 120
    >>> gen = StoryScriptGenerator(llm=llm)
    >>> isinstance(gen, StoryScriptGenerator)
    True
    """

    def __init__(
        self,
        llm: "LLMAdapter",
        language: str = "en",
        target_word_count: int = 1500,
        min_completion_ratio: float = 0.7,
    ) -> None:
        self._llm = llm
        self._language = language
        self._target_word_count = target_word_count
        self._min_completion_ratio = min_completion_ratio

    def generate(
        self,
        topic: str,
        profile: AIStoriesProfile,
        rng: np.random.Generator,
    ) -> Script:
        """Generate a 6-act story script for one video topic.

        Parameters
        ----------
        topic:
            Story premise (for example: ``"haunted lighthouse"``).
        profile:
            AI Stories strategy profile (genre, structure, target size).
        rng:
            Seeded NumPy generator for deterministic keyword selection.

        Returns
        -------
        Script
            Structured script with sections matching ``profile.STORY_STRUCTURE``.

        Raises
        ------
        ValueError
            If topic is blank or generated script is too short.

        Complexity
        ----------
        O(s * (p + t))

        Examples
        --------
        >>> import numpy as np
        >>> from unittest.mock import MagicMock
        >>> llm = MagicMock()
        >>> llm.generate.return_value = "word " * 120
        >>> profile = AIStoriesProfile()
        >>> script = StoryScriptGenerator(llm=llm).generate("lonely forest", profile, np.random.default_rng(42))
        >>> len(script.sections) == len(profile.STORY_STRUCTURE)
        True
        """
        normalized_topic = topic.strip()
        if not normalized_topic:
            raise ValueError("topic must be non-empty")

        section_targets = self._section_word_targets(profile)
        seed_keywords = self._seed_keywords(normalized_topic, profile, rng)
        sections: list[ScriptSection] = []

        for section_name in profile.STORY_STRUCTURE:
            prompt = self._build_prompt(
                topic=normalized_topic,
                profile=profile,
                section=section_name,
                section_word_target=section_targets[section_name],
                seed_keywords=seed_keywords,
                previous_sections=sections,
            )
            max_tokens = max(128, int(section_targets[section_name] * 1.7))
            generated = self._llm.generate(prompt, max_tokens=max_tokens).strip()
            final_text = self._inject_keywords(generated, seed_keywords)
            sections.append(
                ScriptSection(
                    name=section_name,
                    text=final_text,
                    keywords=list(seed_keywords),
                )
            )

        script = Script(
            plan_id=self._story_id(normalized_topic, profile.genre.value),
            sections=sections,
            language=self._language,
        )
        self._validate_script(script, self._target_word_count, self._min_completion_ratio)
        logger.info(
            "StoryScriptGenerator: generated topic=%s genre=%s words=%d",
            normalized_topic,
            profile.genre.value,
            script.total_words,
        )
        return script

    @staticmethod
    def _story_id(topic: str, genre: str) -> str:
        """Build deterministic story ID from topic and genre. O(n).

        Examples
        --------
        >>> StoryScriptGenerator._story_id("Haunted House", "horror")
        'story:horror:haunted-house'
        """
        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-") or "untitled"
        return f"story:{genre}:{slug}"

    def _section_word_targets(self, profile: AIStoriesProfile) -> dict[str, int]:
        """Allocate word budget across the 6 story acts. O(s).

        Examples
        --------
        >>> p = AIStoriesProfile(target_word_count=1500)
        >>> t = StoryScriptGenerator(llm=object())._section_word_targets(p)
        >>> sum(t.values())
        1500
        """
        total = max(600, profile.target_word_count or self._target_word_count)
        ratios = {
            "hook_30s": 0.10,
            "setup_2min": 0.20,
            "conflict_3min": 0.30,
            "twist_2min": 0.18,
            "climax_2min": 0.16,
            "resolution_1min": 0.06,
        }
        targets: dict[str, int] = {}
        consumed = 0
        for section in profile.STORY_STRUCTURE[:-1]:
            value = max(_MIN_SECTION_WORDS, int(total * ratios.get(section, 0.15)))
            targets[section] = value
            consumed += value
        last_section = profile.STORY_STRUCTURE[-1]
        targets[last_section] = max(_MIN_SECTION_WORDS, total - consumed)
        return targets

    def _seed_keywords(
        self,
        topic: str,
        profile: AIStoriesProfile,
        rng: np.random.Generator,
    ) -> list[str]:
        """Select stable keywords for the whole script from topic + genre. O(k).

        Examples
        --------
        >>> import numpy as np
        >>> p = AIStoriesProfile()
        >>> kws = StoryScriptGenerator(llm=object())._seed_keywords("haunted mirror", p, np.random.default_rng(1))
        >>> len(kws) >= 2
        True
        """
        genre_pools: dict[str, list[str]] = {
            "horror": ["suspense", "dark secret", "night", "fear"],
            "drama": ["emotion", "family", "choice", "consequence"],
            "mystery": ["clue", "evidence", "hidden truth", "unknown"],
            "romance": ["connection", "heart", "promise", "destiny"],
            "motivation": ["discipline", "growth", "purpose", "resilience"],
            "historical": ["archive", "legacy", "timeline", "forgotten"],
        }
        base_words = [w for w in re.split(r"\W+", topic.lower()) if len(w) >= 4]
        pool = base_words + genre_pools.get(profile.genre.value, [])
        if not pool:
            return [profile.genre.value, "fictional"]
        sample_size = min(3, len(pool))
        indices = rng.choice(len(pool), size=sample_size, replace=False)
        selected = [pool[int(i)] for i in np.atleast_1d(indices)]
        selected.append("fictional")
        selected.append("18+")
        return list(dict.fromkeys(selected))

    def _build_prompt(
        self,
        topic: str,
        profile: AIStoriesProfile,
        section: str,
        section_word_target: int,
        seed_keywords: list[str],
        previous_sections: list[ScriptSection],
    ) -> str:
        """Compose section prompt with compliance-safe constraints. O(n).

        Examples
        --------
        >>> p = AIStoriesProfile()
        >>> gen = StoryScriptGenerator(llm=object())
        >>> text = gen._build_prompt("haunted attic", p, "hook_30s", 120, ["fictional"], [])
        >>> "fictional" in text.lower()
        True
        """
        continuity = (
            previous_sections[-1].text[:220].replace("\n", " ")
            if previous_sections
            else "Start a fresh story with immediate intrigue."
        )
        keywords = ", ".join(seed_keywords)
        return (
            f"Write section '{section}' of a {profile.genre.value} YouTube narration.\n"
            f"Topic: {topic}\n"
            f"Target length: about {section_word_target} words.\n"
            f"Continuity hint: {continuity}\n"
            f"Use these keywords naturally: {keywords}\n"
            "Safety rules: all characters are adults (18+); no explicit violence; "
            "no medical advice; no real-world claims.\n"
            "Disclosure rule: this is fictional AI-generated entertainment content.\n"
            "Return plain narration text only, no bullet points."
        )

    @staticmethod
    def _inject_keywords(text: str, keywords: list[str]) -> str:
        """Append missing keywords once to support discoverability. O(n * k).

        Examples
        --------
        >>> StoryScriptGenerator._inject_keywords("calm story", ["fictional"])
        'calm story\\n\\nKeywords: fictional'
        """
        lowered = text.lower()
        missing = [kw for kw in keywords if kw.lower() not in lowered]
        if not missing:
            return text
        suffix = ", ".join(missing)
        return f"{text}\n\nKeywords: {suffix}"

    @staticmethod
    def _validate_script(script: Script, target_words: int, min_ratio: float) -> None:
        """Validate generated size and section non-emptiness. O(s).

        Examples
        --------
        >>> s = Script(plan_id="x", sections=[ScriptSection(name="a", text="ok words here")])
        >>> StoryScriptGenerator._validate_script(s, target_words=10, min_ratio=0.1)
        """
        minimum = int(max(300, target_words * min_ratio))
        if script.total_words < minimum:
            raise ValueError(
                f"Story script too short: got {script.total_words} words, expected >= {minimum}"
            )
        for section in script.sections:
            if not section.text.strip():
                raise ValueError(f"Empty story section: {section.name}")
