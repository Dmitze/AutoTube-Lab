"""Hype video idea generator (Phase P13, T-942)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from ytaimbot_ml.niches.hype_characters import (
    HypeCharacter,
    HypeCharactersProfile,
    HypeVideoIdea,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemplatePerformance:
    """Reference engagement for a story template.

    Complexity: O(1).
    """

    template: str
    baseline_views: int


class HypeVideoIdeaGenerator:
    """Generate video ideas from trending characters and proven templates.

    Complexity
    ----------
    generate(): O(c * t) where c = characters, t = templates per character.

    Examples
    --------
    >>> rng = np.random.default_rng(42)
    >>> ideas = HypeVideoIdeaGenerator().generate([], rng)
    >>> ideas
    []
    """

    _BASELINES: tuple[TemplatePerformance, ...] = (
        TemplatePerformance("betrayal_drama", 2_900_000),
        TemplatePerformance("unexpected_hero", 2_100_000),
        TemplatePerformance("family_reunion_tears", 1_900_000),
        TemplatePerformance("jealousy_revenge", 1_700_000),
        TemplatePerformance("forbidden_love", 1_600_000),
        TemplatePerformance("rags_to_riches", 2_300_000),
        TemplatePerformance("sacrifice_for_love", 1_800_000),
    )

    def __init__(
        self,
        profile: HypeCharactersProfile | None = None,
        ideas_per_character: int = 2,
    ) -> None:
        self._profile = profile or HypeCharactersProfile()
        self._ideas_per_character = ideas_per_character

    def generate(
        self,
        characters: list[HypeCharacter],
        rng: np.random.Generator,
    ) -> list[HypeVideoIdea]:
        """Generate ranked ideas for all provided characters.

        Parameters
        ----------
        characters:
            Trending characters, usually from ``TrendingCharacterFetcher``.
        rng:
            Seeded generator used for deterministic template sampling.

        Returns
        -------
        list[HypeVideoIdea]
            Ranked by expected view estimate and character hype score.

        Complexity
        ----------
        O(c * t)
        """
        if not characters:
            return []

        baselines = {item.template: item.baseline_views for item in self._BASELINES}
        template_pool = list(baselines.keys())
        ideas: list[HypeVideoIdea] = []

        for character in characters:
            picks = min(self._ideas_per_character, len(template_pool))
            sampled_idx = rng.choice(len(template_pool), size=picks, replace=False)
            for idx in np.atleast_1d(sampled_idx):
                template = template_pool[int(idx)]
                original_views = int(baselines[template] * max(character.hype_score, 0.5))
                title = self._profile.get_seo_title(character.name, template)
                ideas.append(
                    HypeVideoIdea(
                        character=character,
                        story_template=template,
                        original_views=original_views,
                        title=title,
                        duration_target_seconds=self._profile.min_video_duration_seconds,
                    )
                )

        ideas.sort(
            key=lambda i: (i.expected_views_estimate, i.character.hype_score),
            reverse=True,
        )
        logger.info("HypeVideoIdeaGenerator: generated %d ideas", len(ideas))
        return ideas

