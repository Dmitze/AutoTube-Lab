"""Unit tests for StoryScriptGenerator (Phase P13, T-945)."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock

from ytaimbot_ml.niches.ai_stories import AIStoriesProfile, StoryGenre
from ytaimbot_ml.niches.story_script_generator import StoryScriptGenerator
from ytaimbot_ml.schemas import Script


def _mock_llm(words_per_call: int = 220) -> MagicMock:
    mock = MagicMock()
    mock.generate.side_effect = lambda prompt, max_tokens=512: " ".join(
        ["narration"] * words_per_call
    )
    return mock


def test_generate_returns_script() -> None:
    """generate() returns Script dataclass."""
    llm = _mock_llm()
    gen = StoryScriptGenerator(llm=llm)
    script = gen.generate(
        topic="haunted station",
        profile=AIStoriesProfile(genre=StoryGenre.HORROR),
        rng=np.random.default_rng(42),
    )
    assert isinstance(script, Script)


def test_generate_has_six_sections_in_profile_order() -> None:
    """Section order must follow AIStoriesProfile.STORY_STRUCTURE."""
    llm = _mock_llm()
    profile = AIStoriesProfile(genre=StoryGenre.DRAMA)
    gen = StoryScriptGenerator(llm=llm)
    script = gen.generate("forgotten diary", profile, np.random.default_rng(42))
    assert [section.name for section in script.sections] == profile.STORY_STRUCTURE


def test_generate_calls_llm_for_each_section() -> None:
    """LLM is called exactly once per section."""
    llm = _mock_llm()
    profile = AIStoriesProfile()
    gen = StoryScriptGenerator(llm=llm)
    gen.generate("abandoned hotel", profile, np.random.default_rng(42))
    assert llm.generate.call_count == len(profile.STORY_STRUCTURE)


def test_generate_is_deterministic_for_same_seed() -> None:
    """Same seed yields same keyword selection."""
    llm1 = _mock_llm()
    llm2 = _mock_llm()
    profile = AIStoriesProfile(genre=StoryGenre.MYSTERY)

    s1 = StoryScriptGenerator(llm=llm1).generate(
        "clock tower secret", profile, np.random.default_rng(7)
    )
    s2 = StoryScriptGenerator(llm=llm2).generate(
        "clock tower secret", profile, np.random.default_rng(7)
    )
    assert s1.sections[0].keywords == s2.sections[0].keywords


def test_generate_total_words_above_minimum_ratio() -> None:
    """Generated script should pass size validation."""
    llm = _mock_llm(words_per_call=210)
    gen = StoryScriptGenerator(llm=llm, target_word_count=1200, min_completion_ratio=0.7)
    script = gen.generate("silent valley", AIStoriesProfile(), np.random.default_rng(1))
    assert script.total_words >= 840


def test_generate_blank_topic_raises() -> None:
    """Blank topic is rejected."""
    llm = _mock_llm()
    gen = StoryScriptGenerator(llm=llm)
    with pytest.raises(ValueError, match="topic must be non-empty"):
        gen.generate("   ", AIStoriesProfile(), np.random.default_rng(1))


def test_generate_short_script_raises() -> None:
    """Too-short generated output raises ValueError."""
    llm = _mock_llm(words_per_call=5)
    gen = StoryScriptGenerator(llm=llm, target_word_count=1500, min_completion_ratio=0.7)
    with pytest.raises(ValueError, match="Story script too short"):
        gen.generate("midnight train", AIStoriesProfile(), np.random.default_rng(3))


def test_prompt_contains_adult_and_fictional_safety_rules() -> None:
    """Prompt enforces compliance-safe boundaries."""
    llm = _mock_llm()
    profile = AIStoriesProfile(genre=StoryGenre.HORROR)
    gen = StoryScriptGenerator(llm=llm)
    gen.generate("attic whisper", profile, np.random.default_rng(11))
    first_prompt = llm.generate.call_args_list[0].args[0].lower()
    assert "18+" in first_prompt
    assert "fictional ai-generated" in first_prompt


def test_story_id_slug_format() -> None:
    """story_id uses stable slug format."""
    value = StoryScriptGenerator._story_id("Haunted House #13", "horror")
    assert value == "story:horror:haunted-house-13"
