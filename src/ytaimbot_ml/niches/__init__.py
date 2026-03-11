"""Niche-specific content strategy modules."""

from ytaimbot_ml.niches.ghibli_asmr import GhibliASMRProfile, SubNiche
from ytaimbot_ml.niches.character_registry import Character, CharacterRegistry
from ytaimbot_ml.niches.scene_planner import Scene, ScenePlanner
from ytaimbot_ml.niches.ghibli_seo import GhibliSEO, SeasonalBoost
from ytaimbot_ml.niches.hype_characters import (
    HypeCharacter,
    HypeCharactersProfile,
    HypeVideoIdea,
    HypeSource,
)
from ytaimbot_ml.niches.ai_stories import AIStoriesProfile, StoryGenre

__all__ = [
    "GhibliASMRProfile",
    "SubNiche",
    "Character",
    "CharacterRegistry",
    "Scene",
    "ScenePlanner",
    "GhibliSEO",
    "SeasonalBoost",
    "HypeCharacter",
    "HypeCharactersProfile",
    "HypeVideoIdea",
    "HypeSource",
    "AIStoriesProfile",
    "StoryGenre",
]
