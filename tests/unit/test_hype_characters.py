"""Unit tests for Hype niche modules (P13: T-941/T-942/T-943/T-950)."""

from __future__ import annotations

import numpy as np

from ytaimbot_ml.niches.hype_characters import HypeCharactersProfile
from ytaimbot_ml.niches.hype_idea_generator import HypeVideoIdeaGenerator
from ytaimbot_ml.niches.hype_seo import HypeSEO
from ytaimbot_ml.niches.trend_character_fetcher import TrendingCharacterFetcher
from ytaimbot_ml.schemas import TrendSignal


class _StubTrendSource:
    """Deterministic in-memory trend source used by tests only."""

    def fetch(self) -> list[TrendSignal]:
        return [
            TrendSignal("1", "Judy Hopps Zootopia 2", 0.95, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("2", "Nick Wilde viral", 0.91, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("3", "Batman comeback", 0.88, "youtube_search", "2026-01-01T00:00:00Z"),
            TrendSignal("4", "Spider Man new arc", 0.84, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("5", "Naruto reboot", 0.80, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("6", "Goku transformation", 0.78, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("7", "unknown phrase", 0.99, "google_trends", "2026-01-01T00:00:00Z"),
        ]


def test_hype_profile_title_lte_100_and_has_emoji() -> None:
    """T-950 acceptance: title <= 100 chars and contains CTR emoji."""
    profile = HypeCharactersProfile()
    title = profile.get_seo_title("Judy Hopps", "betrayal_drama")
    assert len(title) <= 100
    assert any(ch in title for ch in ["😭", "😮", "😢", "💔", "🔥", "😤"])


def test_hype_profile_tags_count_gte_15() -> None:
    """T-950 acceptance: tags list has at least 15 entries."""
    profile = HypeCharactersProfile()
    tags = profile.get_seo_tags("Judy Hopps", "Zootopia 2")
    assert len(tags) >= 15


def test_trending_character_fetcher_returns_top_hot_characters() -> None:
    """Fetcher should return at least 5 characters with hype_score >= 0.7."""
    fetcher = TrendingCharacterFetcher(
        source=_StubTrendSource(),
        min_hype_score=0.7,
        top_k=10,
    )
    out = fetcher.fetch()
    assert len(out) >= 5
    assert all(c.hype_score >= 0.7 for c in out)


def test_trending_character_fetcher_sorted_desc() -> None:
    """Output is ranked by hype score descending."""
    out = TrendingCharacterFetcher(source=_StubTrendSource()).fetch()
    scores = [c.hype_score for c in out]
    assert scores == sorted(scores, reverse=True)


def test_hype_idea_generator_generates_nonempty_ideas() -> None:
    """Idea generator should emit ideas for fetched characters."""
    chars = TrendingCharacterFetcher(source=_StubTrendSource()).fetch()
    ideas = HypeVideoIdeaGenerator().generate(chars, np.random.default_rng(42))
    assert len(ideas) > 0
    assert all(i.duration_target_seconds >= 480 for i in ideas)


def test_hype_idea_generator_deterministic_with_seed() -> None:
    """Same seed and same input produce same top template ordering."""
    chars = TrendingCharacterFetcher(source=_StubTrendSource()).fetch()
    gen = HypeVideoIdeaGenerator()
    a = gen.generate(chars, np.random.default_rng(42))
    b = gen.generate(chars, np.random.default_rng(42))
    assert [x.story_template for x in a[:5]] == [x.story_template for x in b[:5]]


def test_hype_seo_title_and_tags_delegate_to_profile() -> None:
    """HypeSEO wraps profile title/tags generation."""
    seo = HypeSEO()
    title = seo.title("Batman", "unexpected_hero")
    tags = seo.tags("Batman", "DC")
    assert len(title) <= 100
    assert len(tags) >= 15


def test_hype_seo_thumbnail_contains_character_and_labels() -> None:
    """Thumbnail template includes character identity and two labels."""
    char = TrendingCharacterFetcher(source=_StubTrendSource()).fetch()[0]
    tpl = HypeSEO().thumbnail(char, "betrayal_drama")
    assert char.name in tpl.prompt
    assert len(tpl.labels) == 2
    assert tpl.labels[0] == "WHAT HAPPENED?!"

