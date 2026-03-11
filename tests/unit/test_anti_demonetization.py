"""Tests for anti-demonetization protection (Phase P12).

Tests:
  test_disclaimer_in_description       : generate_description() contains AI disclaimer
  test_trigger_topics_detected         : contains_trigger_topics catches known triggers
  test_trigger_topics_safe_text        : safe text returns False
  test_blacklist_is_safe               : safe topic passes TopicBlacklist
  test_blacklist_blocks_trigger        : pregnant/injury/etc blocked
  test_blacklist_get_violations        : returns list of violations
  test_disclaimer_year_current         : disclaimer contains current year
  test_hype_profile_title_length       : title <= 100 chars
  test_hype_profile_tags_count         : tags >= 15
  test_hype_profile_is_hot             : hype_score >= 0.7 → is_hot
  test_ai_stories_llm_prompt           : prompt contains genre and word count
  test_ai_stories_title_length         : title <= 100 chars
  test_ai_stories_tags_count           : tags >= 15
"""

from __future__ import annotations

import datetime

import pytest

from ytaimbot_ml.niches.ghibli_asmr import SubNiche
from ytaimbot_ml.niches.ghibli_seo import GhibliSEO
from ytaimbot_ml.quality.bayes_filter import TopicBlacklist
from ytaimbot_ml.niches.hype_characters import (
    HypeCharacter,
    HypeCharactersProfile,
    HypeVideoIdea,
    HypeSource,
)
from ytaimbot_ml.niches.ai_stories import AIStoriesProfile, StoryGenre


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def seo() -> GhibliSEO:
    return GhibliSEO(sub_niche=SubNiche.VILLAGE_LIFE)


@pytest.fixture
def blacklist() -> TopicBlacklist:
    return TopicBlacklist()


@pytest.fixture
def hype_profile() -> HypeCharactersProfile:
    return HypeCharactersProfile()


@pytest.fixture
def judy() -> HypeCharacter:
    return HypeCharacter(
        name="Judy Hopps",
        franchise="Zootopia 2",
        hype_score=0.95,
        source=HypeSource.YOUTUBE_TRENDING,
    )


@pytest.fixture
def stories_horror() -> AIStoriesProfile:
    return AIStoriesProfile(genre=StoryGenre.HORROR)


@pytest.fixture
def stories_drama() -> AIStoriesProfile:
    return AIStoriesProfile(genre=StoryGenre.DRAMA)


# ---------------------------------------------------------------------------
# 1a — GhibliSEO disclaimer tests
# ---------------------------------------------------------------------------

def test_disclaimer_in_description(seo: GhibliSEO) -> None:
    """generate_description() must always contain the AI disclaimer."""
    desc = seo.generate_description("morning in the village")
    assert "Artificial Intelligence" in desc
    assert "All depicted characters are adults (18+)" in desc
    assert "AI-generated creative content" in desc


def test_disclaimer_year_current(seo: GhibliSEO) -> None:
    """Disclaimer must contain the current year."""
    desc = seo.generate_description("cozy forest path")
    current_year = str(datetime.datetime.now(datetime.timezone.utc).year)
    assert current_year in desc


def test_trigger_topics_detected(seo: GhibliSEO) -> None:
    """contains_trigger_topics returns True for known demonetization triggers."""
    assert seo.contains_trigger_topics("A pregnant character in the village")
    assert seo.contains_trigger_topics("Scene shows blood and injury")
    assert seo.contains_trigger_topics("Breaking news: Ghibli update!")
    assert seo.contains_trigger_topics("Medical advice for sleepers")


def test_trigger_topics_safe_text(seo: GhibliSEO) -> None:
    """contains_trigger_topics returns False for entirely safe text."""
    assert not seo.contains_trigger_topics("Cozy Ghibli village morning ASMR")
    assert not seo.contains_trigger_topics("Relaxing rain sounds, no talking")


# ---------------------------------------------------------------------------
# 1b — TopicBlacklist tests
# ---------------------------------------------------------------------------

def test_blacklist_is_safe(blacklist: TopicBlacklist) -> None:
    """Safe topics pass the blacklist."""
    assert blacklist.is_safe("cozy village ASMR video")
    assert blacklist.is_safe("Ghibli relaxing sounds, no talking")


def test_blacklist_blocks_trigger(blacklist: TopicBlacklist) -> None:
    """Demonetization-risk topics are blocked."""
    assert not blacklist.is_safe("pregnant woman animated scene")
    assert not blacklist.is_safe("this really happened in the village")
    assert not blacklist.is_safe("breaking news alert")
    assert not blacklist.is_safe("surgery scene included")
    assert not blacklist.is_safe("medical advice for insomnia")


def test_blacklist_get_violations(blacklist: TopicBlacklist) -> None:
    """get_violations returns each matched pattern."""
    violations = blacklist.get_violations("surgery and medical advice in the story")
    assert "surgery" in violations
    assert "medical advice" in violations
    assert len(violations) == 2


def test_blacklist_get_violations_empty_for_safe(blacklist: TopicBlacklist) -> None:
    """get_violations returns empty list for safe text."""
    assert blacklist.get_violations("gentle forest morning sounds") == []


def test_blacklist_add_pattern(blacklist: TopicBlacklist) -> None:
    """add_pattern extends the blacklist at runtime."""
    blacklist.add_pattern("dangerous stunt")
    assert not blacklist.is_safe("This dangerous stunt video is amazing")
    assert "dangerous stunt" in blacklist.get_violations("dangerous stunt challenge")


def test_blacklist_custom_patterns() -> None:
    """Custom patterns at construction time are also blocked."""
    bl = TopicBlacklist(custom_patterns=["cursed image", "shock content"])
    assert not bl.is_safe("Reacting to cursed image compilations")
    assert not bl.is_safe("shock content warning inside")


# ---------------------------------------------------------------------------
# 2a — HypeCharactersProfile tests
# ---------------------------------------------------------------------------

def test_hype_profile_title_length(hype_profile: HypeCharactersProfile) -> None:
    """get_seo_title always returns a title ≤ 100 chars."""
    for template in HypeCharactersProfile.PROVEN_STORY_TEMPLATES:
        title = hype_profile.get_seo_title("Judy Hopps", template)
        assert len(title) <= 100, f"Title too long for template {template!r}: {title!r}"


def test_hype_profile_tags_count(hype_profile: HypeCharactersProfile, judy: HypeCharacter) -> None:
    """get_seo_tags returns at least 15 tags."""
    tags = hype_profile.get_seo_tags(judy.name, judy.franchise)
    assert len(tags) >= 15


def test_hype_profile_is_hot(judy: HypeCharacter) -> None:
    """HypeCharacter with hype_score >= 0.7 should be considered hot."""
    assert judy.is_hot


def test_hype_character_not_hot() -> None:
    """HypeCharacter with hype_score < 0.7 should not be hot."""
    cold = HypeCharacter("Old Fox", "Zootopia 1", 0.5, HypeSource.MANUAL)
    assert not cold.is_hot


def test_hype_video_idea_expected_views(judy: HypeCharacter) -> None:
    """expected_views_estimate is 50% of original_views."""
    idea = HypeVideoIdea(character=judy, story_template="betrayal_drama", original_views=3_000_000)
    assert idea.expected_views_estimate == 1_500_000


def test_hype_profile_title_contains_character_name(hype_profile: HypeCharactersProfile) -> None:
    """Generated title must include the character name."""
    title = hype_profile.get_seo_title("Nick Wilde", "unexpected_hero")
    assert "Nick Wilde" in title


def test_hype_profile_tags_contain_character(
    hype_profile: HypeCharactersProfile,
    judy: HypeCharacter,
) -> None:
    """Tags must include both character name and franchise."""
    tags = hype_profile.get_seo_tags(judy.name, judy.franchise)
    assert judy.name in tags
    assert judy.franchise in tags


# ---------------------------------------------------------------------------
# 2b — AIStoriesProfile tests
# ---------------------------------------------------------------------------

def test_ai_stories_llm_prompt(stories_horror: AIStoriesProfile) -> None:
    """get_llm_prompt includes genre name and word count."""
    prompt = stories_horror.get_llm_prompt("haunted lighthouse")
    assert "horror" in prompt
    assert str(stories_horror.target_word_count) in prompt
    assert "haunted lighthouse" in prompt


def test_ai_stories_title_length(stories_horror: AIStoriesProfile) -> None:
    """get_seo_title returns a title ≤ 100 chars."""
    title = stories_horror.get_seo_title("abandoned lighthouse keeper")
    assert len(title) <= 100


def test_ai_stories_title_contains_topic(stories_drama: AIStoriesProfile) -> None:
    """get_seo_title includes the provided topic."""
    title = stories_drama.get_seo_title("betrayal at the office")
    assert "betrayal at the office" in title


def test_ai_stories_tags_count(stories_horror: AIStoriesProfile) -> None:
    """get_seo_tags returns at least 15 tags."""
    tags = stories_horror.get_seo_tags("haunted house")
    assert len(tags) >= 15


def test_ai_stories_tags_contain_topic(stories_drama: AIStoriesProfile) -> None:
    """get_seo_tags must include the topic string."""
    tags = stories_drama.get_seo_tags("lost city mystery")
    assert "lost city mystery" in tags


def test_ai_stories_genre_specific_tags(stories_horror: AIStoriesProfile) -> None:
    """Horror profile must include horror-specific tags."""
    tags = stories_horror.get_seo_tags("cemetery at midnight")
    assert "horror story" in tags or "scary story" in tags


def test_ai_stories_disclaimer_present(stories_horror: AIStoriesProfile) -> None:
    """AI_DISCLAIMER must be non-empty and mark content as fictional."""
    assert "fictional" in stories_horror.AI_DISCLAIMER.lower()
    assert "AI" in stories_horror.AI_DISCLAIMER
