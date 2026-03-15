"""Unit tests for AIStoriesProfile (Phase P13, T-951)."""

from __future__ import annotations

from ytaimbot_ml.niches.ai_stories import AIStoriesProfile, StoryGenre


def test_llm_prompt_contains_genre_word_count_and_structure() -> None:
    """Prompt includes genre, target words, and 6-act structure hints."""
    profile = AIStoriesProfile(genre=StoryGenre.HORROR, target_word_count=1500)
    prompt = profile.get_llm_prompt("haunted lighthouse")

    assert "horror" in prompt.lower()
    assert "1500" in prompt
    assert "hook" in prompt.lower()
    assert "twist" in prompt.lower()
    assert "resolution" in prompt.lower()


def test_story_structure_has_six_acts() -> None:
    """AIStoriesProfile.STORY_STRUCTURE must define exactly 6 acts."""
    profile = AIStoriesProfile()
    assert len(profile.STORY_STRUCTURE) == 6
    assert profile.STORY_STRUCTURE[0] == "hook_30s"
    assert profile.STORY_STRUCTURE[-1] == "resolution_1min"


def test_seo_title_length_is_lte_100() -> None:
    """SEO title is clipped to YouTube-friendly length."""
    profile = AIStoriesProfile(genre=StoryGenre.MYSTERY)
    title = profile.get_seo_title("The Case of the Door That Opened at Midnight Every Day")
    assert len(title) <= 100


def test_seo_tags_returns_minimum_15_tags() -> None:
    """Tag set contains enough search terms for discoverability."""
    profile = AIStoriesProfile(genre=StoryGenre.DRAMA)
    tags = profile.get_seo_tags("forbidden letter")
    assert len(tags) >= 15


def test_ai_disclaimer_mentions_fictional_and_ai() -> None:
    """Disclosure text includes AI generation and fictional warning."""
    disclaimer = AIStoriesProfile.AI_DISCLAIMER.lower()
    assert "ai-generated" in disclaimer or "created with ai" in disclaimer
    assert "fictional" in disclaimer
