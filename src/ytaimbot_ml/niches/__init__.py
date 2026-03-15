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
from ytaimbot_ml.niches.story_script_generator import StoryScriptGenerator
from ytaimbot_ml.niches.trend_character_fetcher import (
    CharacterAlias,
    TrendingCharacterFetcher,
)
from ytaimbot_ml.niches.hype_idea_generator import (
    HypeVideoIdeaGenerator,
    TemplatePerformance,
)
from ytaimbot_ml.niches.hype_seo import HypeSEO, HypeThumbnailTemplate

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
    "StoryScriptGenerator",
    "CharacterAlias",
    "TrendingCharacterFetcher",
    "HypeVideoIdeaGenerator",
    "TemplatePerformance",
    "HypeSEO",
    "HypeThumbnailTemplate",
]
