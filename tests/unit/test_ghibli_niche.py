"""Unit tests for Ghibli ASMR niche modules (Phase P11, T-910–T-912).

Tests:
  test_profile_duration           : duration = scenes × seconds
  test_profile_scene_prompt       : prompt contains sub_niche name
  test_character_registry_add_get : add/get round-trip
  test_character_registry_remove  : remove returns True, second remove False
  test_character_imagen_fragment  : fragment = "name: description"
  test_scene_planner_parse_50     : parse 50 lines → 50 scenes
  test_scene_planner_ids_sequential: scene_ids are 1..50
  test_scene_planner_template     : template fallback produces n scenes (deterministic)
  test_scene_planner_imagen_prompt: contains style prefix + scene prompt
  test_timeline_start_end         : to_timeline() start/end are sequential
  test_ghibli_seo_title_length    : title ≤ 100 chars
  test_ghibli_seo_must_have       : title contains ≥ 1 MUST_HAVE keyword
  test_ghibli_seo_tags_count      : generate_tags returns ≥ 15 tags
  test_seasonal_boost_winter      : date(2026, 1, 5) → season="winter"
  test_seasonal_boost_summer      : date(2026, 7, 15) → season="summer"
  test_seo_score_range            : score_title returns value in [0, 1]
"""

from __future__ import annotations

import datetime

import numpy as np
import pytest

from ytaimbot_ml.niches.character_registry import Character, CharacterRegistry
from ytaimbot_ml.niches.ghibli_asmr import GhibliASMRProfile, SubNiche
from ytaimbot_ml.niches.ghibli_seo import GhibliSEO, SeasonalBoost
from ytaimbot_ml.niches.scene_planner import Scene, ScenePlanner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def profile() -> GhibliASMRProfile:
    """Default Ghibli ASMR profile (50 scenes × 7 s)."""
    return GhibliASMRProfile(sub_niche=SubNiche.VILLAGE_LIFE)


@pytest.fixture()
def registry() -> CharacterRegistry:
    """Empty CharacterRegistry for channel 'ch_test'."""
    return CharacterRegistry(channel_id="ch_test")


@pytest.fixture()
def registry_with_char() -> CharacterRegistry:
    """Registry pre-populated with one character."""
    reg = CharacterRegistry(channel_id="ch_test")
    reg.add(
        Character(
            char_id="c1",
            channel_id="ch_test",
            name="Hanna",
            description="elderly woman, white hair bun, warm apron, blue eyes",
        )
    )
    return reg


@pytest.fixture()
def planner(profile: GhibliASMRProfile, registry: CharacterRegistry) -> ScenePlanner:
    """ScenePlanner with default profile and empty registry."""
    return ScenePlanner(profile=profile, registry=registry)


@pytest.fixture()
def rng() -> np.random.Generator:
    """Seeded RNG for deterministic template tests (seed=42)."""
    return np.random.default_rng(42)


@pytest.fixture()
def seo() -> GhibliSEO:
    """GhibliSEO instance for VILLAGE_LIFE sub-niche."""
    return GhibliSEO(sub_niche=SubNiche.VILLAGE_LIFE)


@pytest.fixture()
def seasonal_boost() -> SeasonalBoost:
    """SeasonalBoost instance."""
    return SeasonalBoost()


# ---------------------------------------------------------------------------
# GhibliASMRProfile tests
# ---------------------------------------------------------------------------


class TestGhibliASMRProfile:
    def test_profile_duration(self, profile: GhibliASMRProfile) -> None:
        """duration_seconds == scenes_per_video × seconds_per_scene."""
        assert profile.duration_seconds == profile.scenes_per_video * profile.seconds_per_scene

    def test_profile_duration_default(self) -> None:
        """Default profile: 50 × 7 = 350 seconds."""
        p = GhibliASMRProfile()
        assert p.duration_seconds == 350

    def test_profile_duration_minutes(self) -> None:
        """duration_minutes == duration_seconds / 60."""
        p = GhibliASMRProfile()
        assert abs(p.duration_minutes - 350 / 60) < 1e-9

    def test_profile_scene_prompt_contains_subniche(self, profile: GhibliASMRProfile) -> None:
        """scene_prompt_prefix() contains the sub-niche name."""
        prefix = profile.scene_prompt_prefix()
        assert "village life" in prefix.lower()

    def test_profile_scene_prompt_contains_style_tag(self, profile: GhibliASMRProfile) -> None:
        """scene_prompt_prefix() contains at least one style tag."""
        prefix = profile.scene_prompt_prefix()
        assert "Studio Ghibli style" in prefix

    def test_profile_llm_prompt_contains_scene_count(self, profile: GhibliASMRProfile) -> None:
        """llm_system_prompt() mentions the configured scene count."""
        prompt = profile.llm_system_prompt()
        assert str(profile.scenes_per_video) in prompt

    def test_profile_llm_prompt_contains_ghibli(self, profile: GhibliASMRProfile) -> None:
        """llm_system_prompt() contains 'Ghibli'."""
        assert "Ghibli" in profile.llm_system_prompt()

    def test_subniche_winter(self) -> None:
        """SubNiche.WINTER_COZY round-trips through value."""
        assert SubNiche("winter_cozy") is SubNiche.WINTER_COZY

    def test_profile_custom_scenes(self) -> None:
        """Custom scenes_per_video and seconds_per_scene are respected."""
        p = GhibliASMRProfile(scenes_per_video=10, seconds_per_scene=5)
        assert p.duration_seconds == 50


# ---------------------------------------------------------------------------
# Character / CharacterRegistry tests
# ---------------------------------------------------------------------------


class TestCharacter:
    def test_character_imagen_fragment(self) -> None:
        """imagen_prompt_fragment = 'name: description'."""
        c = Character(
            char_id="c1",
            channel_id="ch1",
            name="Hanna",
            description="elderly woman, white hair bun, warm apron, blue eyes",
        )
        assert c.imagen_prompt_fragment == "Hanna: elderly woman, white hair bun, warm apron, blue eyes"

    def test_character_imagen_fragment_simple(self) -> None:
        """Short description produces expected fragment."""
        c = Character("c2", "ch1", "Kiri", "young girl, red dress")
        assert c.imagen_prompt_fragment == "Kiri: young girl, red dress"


class TestCharacterRegistry:
    def test_registry_add_get(self, registry: CharacterRegistry) -> None:
        """add() then get() round-trip returns the same character."""
        char = Character("c1", "ch_test", "Hanna", "elderly woman")
        registry.add(char)
        result = registry.get("c1")
        assert result is not None
        assert result.name == "Hanna"

    def test_registry_get_missing_returns_none(self, registry: CharacterRegistry) -> None:
        """get() on unknown ID returns None."""
        assert registry.get("nonexistent") is None

    def test_registry_remove_returns_true(self, registry: CharacterRegistry) -> None:
        """remove() returns True when character exists."""
        registry.add(Character("c1", "ch_test", "Hanna", "elderly woman"))
        assert registry.remove("c1") is True

    def test_registry_remove_returns_false_on_second_call(self, registry: CharacterRegistry) -> None:
        """Second remove() on same ID returns False."""
        registry.add(Character("c1", "ch_test", "Hanna", "elderly woman"))
        registry.remove("c1")
        assert registry.remove("c1") is False

    def test_registry_list_all_empty(self, registry: CharacterRegistry) -> None:
        """Empty registry yields empty list."""
        assert registry.list_all() == []

    def test_registry_list_all_count(self, registry: CharacterRegistry) -> None:
        """list_all() returns all added characters."""
        registry.add(Character("c1", "ch_test", "Hanna", "elderly woman"))
        registry.add(Character("c2", "ch_test", "Kiri", "young girl"))
        assert len(registry.list_all()) == 2

    def test_registry_to_dict_structure(self, registry_with_char: CharacterRegistry) -> None:
        """to_dict() returns expected keys."""
        d = registry_with_char.to_dict()
        assert d["channel_id"] == "ch_test"
        assert len(d["characters"]) == 1
        assert d["characters"][0]["name"] == "Hanna"

    def test_registry_from_dict_roundtrip(self, registry_with_char: CharacterRegistry) -> None:
        """from_dict(to_dict()) round-trip preserves character data."""
        d = registry_with_char.to_dict()
        restored = CharacterRegistry.from_dict(d, "ch_test")
        char = restored.get("c1")
        assert char is not None
        assert char.name == "Hanna"

    def test_registry_load_from_storage_no_storage(self, registry: CharacterRegistry) -> None:
        """load_from_storage() returns 0 when no storage is configured."""
        assert registry.load_from_storage() == 0


# ---------------------------------------------------------------------------
# Scene / ScenePlanner tests
# ---------------------------------------------------------------------------


class TestScene:
    def test_scene_label(self) -> None:
        """Scene.label returns 'Scene {id}/{total}'."""
        s = Scene(scene_id=1, total_scenes=50, prompt="test")
        assert s.label == "Scene 1/50"

    def test_scene_label_mid(self) -> None:
        """Scene label works for middle scenes."""
        s = Scene(scene_id=25, total_scenes=50, prompt="test")
        assert s.label == "Scene 25/50"


class TestScenePlanner:
    def test_scene_planner_parse_50(self, planner: ScenePlanner) -> None:
        """parse_llm_output with 50 lines → 50 scenes."""
        raw = "\n".join(f"Scene description {i}" for i in range(50))
        scenes = planner.parse_llm_output(raw)
        assert len(scenes) == 50

    def test_scene_planner_ids_sequential(self, planner: ScenePlanner) -> None:
        """Parsed scene_ids are 1-indexed and sequential."""
        raw = "\n".join(f"Desc {i}" for i in range(50))
        scenes = planner.parse_llm_output(raw)
        ids = [s.scene_id for s in scenes]
        assert ids == list(range(1, 51))

    def test_scene_planner_parse_fewer_lines(self, planner: ScenePlanner) -> None:
        """parse_llm_output with < 50 lines returns fewer scenes."""
        raw = "\n".join(f"Desc {i}" for i in range(10))
        scenes = planner.parse_llm_output(raw)
        assert len(scenes) == 10

    def test_scene_planner_parse_ignores_empty_lines(self, planner: ScenePlanner) -> None:
        """Empty lines in LLM output are skipped."""
        raw = "\n\n".join(f"Desc {i}" for i in range(20))
        scenes = planner.parse_llm_output(raw)
        assert len(scenes) == 20

    def test_scene_planner_template_count(
        self, planner: ScenePlanner, rng: np.random.Generator
    ) -> None:
        """generate_template_scenes produces scenes_per_video scenes."""
        scenes = planner.generate_template_scenes("forest morning", rng)
        assert len(scenes) == planner._profile.scenes_per_video

    def test_scene_planner_template_deterministic(
        self, profile: GhibliASMRProfile, registry: CharacterRegistry
    ) -> None:
        """generate_template_scenes is deterministic with the same seed."""
        p1 = ScenePlanner(profile, registry)
        p2 = ScenePlanner(profile, registry)
        s1 = p1.generate_template_scenes("morning", np.random.default_rng(42))
        s2 = p2.generate_template_scenes("morning", np.random.default_rng(42))
        assert [s.prompt for s in s1] == [s.prompt for s in s2]

    def test_scene_planner_template_ids_sequential(
        self, planner: ScenePlanner, rng: np.random.Generator
    ) -> None:
        """Template-generated scene_ids are 1-indexed and sequential."""
        scenes = planner.generate_template_scenes("village morning", rng)
        ids = [s.scene_id for s in scenes]
        assert ids == list(range(1, planner._profile.scenes_per_video + 1))

    def test_scene_planner_imagen_prompt_contains_prefix(
        self, planner: ScenePlanner
    ) -> None:
        """build_imagen_prompt() contains the style prefix."""
        scene = Scene(1, 50, "Hanna pours tea by a frosted window")
        prompt = planner.build_imagen_prompt(scene)
        assert "Studio Ghibli style" in prompt

    def test_scene_planner_imagen_prompt_contains_scene_text(
        self, planner: ScenePlanner
    ) -> None:
        """build_imagen_prompt() contains the original scene prompt text."""
        scene = Scene(1, 50, "Hanna pours tea by a frosted window")
        prompt = planner.build_imagen_prompt(scene)
        assert "Hanna pours tea" in prompt

    def test_scene_planner_imagen_prompt_with_character(
        self, profile: GhibliASMRProfile, registry_with_char: CharacterRegistry
    ) -> None:
        """build_imagen_prompt() includes character fragment when char_id present."""
        planner = ScenePlanner(profile=profile, registry=registry_with_char)
        scene = Scene(1, 50, "test scene", character_ids=["c1"])
        prompt = planner.build_imagen_prompt(scene)
        assert "Hanna: elderly woman" in prompt

    def test_timeline_start_end(self, planner: ScenePlanner) -> None:
        """to_timeline() produces sequential, non-overlapping start/end times."""
        scenes = [Scene(i + 1, 3, f"desc {i}", duration_seconds=7) for i in range(3)]
        tl = planner.to_timeline(scenes)
        assert tl[0]["start_s"] == 0
        assert tl[0]["end_s"] == 7
        assert tl[1]["start_s"] == 7
        assert tl[1]["end_s"] == 14
        assert tl[2]["start_s"] == 14
        assert tl[2]["end_s"] == 21

    def test_timeline_length_matches_scenes(self, planner: ScenePlanner) -> None:
        """to_timeline() returns same number of entries as input scenes."""
        scenes = [Scene(i + 1, 10, f"desc {i}") for i in range(10)]
        tl = planner.to_timeline(scenes)
        assert len(tl) == 10

    def test_timeline_contains_label(self, planner: ScenePlanner) -> None:
        """Each timeline entry has a non-empty 'label' key."""
        scenes = [Scene(1, 5, "test")]
        tl = planner.to_timeline(scenes)
        assert tl[0]["label"] == "Scene 1/5"


# ---------------------------------------------------------------------------
# SeasonalBoost tests
# ---------------------------------------------------------------------------


class TestSeasonalBoost:
    def test_seasonal_boost_winter_january(self, seasonal_boost: SeasonalBoost) -> None:
        """date(2026, 1, 5) maps to 'winter'."""
        assert seasonal_boost.get_season(datetime.date(2026, 1, 5)) == "winter"

    def test_seasonal_boost_winter_december(self, seasonal_boost: SeasonalBoost) -> None:
        """date(2026, 12, 15) maps to 'winter'."""
        assert seasonal_boost.get_season(datetime.date(2026, 12, 15)) == "winter"

    def test_seasonal_boost_spring(self, seasonal_boost: SeasonalBoost) -> None:
        """date(2026, 4, 10) maps to 'spring'."""
        assert seasonal_boost.get_season(datetime.date(2026, 4, 10)) == "spring"

    def test_seasonal_boost_summer(self, seasonal_boost: SeasonalBoost) -> None:
        """date(2026, 7, 15) maps to 'summer'."""
        assert seasonal_boost.get_season(datetime.date(2026, 7, 15)) == "summer"

    def test_seasonal_boost_autumn(self, seasonal_boost: SeasonalBoost) -> None:
        """date(2026, 10, 1) maps to 'autumn'."""
        assert seasonal_boost.get_season(datetime.date(2026, 10, 1)) == "autumn"

    def test_seasonal_boost_keywords_winter(self, seasonal_boost: SeasonalBoost) -> None:
        """get_keywords() for winter date includes 'cozy winter cabin'."""
        kws = seasonal_boost.get_keywords(datetime.date(2026, 1, 5))
        assert "cozy winter cabin" in kws

    def test_seasonal_boost_keywords_summer(self, seasonal_boost: SeasonalBoost) -> None:
        """get_keywords() for summer date includes 'fireflies ASMR'."""
        kws = seasonal_boost.get_keywords(datetime.date(2026, 7, 15))
        assert "fireflies ASMR" in kws

    def test_seasonal_boost_keywords_count(self, seasonal_boost: SeasonalBoost) -> None:
        """get_keywords() returns exactly 4 keywords for every season."""
        for month in [1, 4, 7, 10]:
            kws = seasonal_boost.get_keywords(datetime.date(2026, month, 1))
            assert len(kws) == 4


# ---------------------------------------------------------------------------
# GhibliSEO tests
# ---------------------------------------------------------------------------


class TestGhibliSEO:
    def test_ghibli_seo_title_length(self, seo: GhibliSEO) -> None:
        """generate_title() returns a title ≤ 100 characters."""
        title = seo.generate_title(topic="morning on the hill", season_keywords=["spring rain"])
        assert len(title) <= 100

    def test_ghibli_seo_must_have_in_title(self, seo: GhibliSEO) -> None:
        """Title contains at least 1 MUST_HAVE keyword."""
        title = seo.generate_title(topic="morning on the hill")
        title_lower = title.lower()
        has_any = any(kw.lower() in title_lower for kw in GhibliSEO.MUST_HAVE_KEYWORDS)
        assert has_any

    def test_ghibli_seo_title_is_string(self, seo: GhibliSEO) -> None:
        """generate_title() returns a non-empty string."""
        title = seo.generate_title(topic="cozy morning")
        assert isinstance(title, str) and len(title) > 0

    def test_ghibli_seo_tags_count(self, seo: GhibliSEO) -> None:
        """generate_tags() returns ≥ 15 tags."""
        tags = seo.generate_tags(topic="forest morning")
        assert len(tags) >= 15

    def test_ghibli_seo_tags_contains_must_have(self, seo: GhibliSEO) -> None:
        """generate_tags() result includes 'Ghibli ASMR'."""
        tags = seo.generate_tags(topic="test")
        assert "Ghibli ASMR" in tags

    def test_ghibli_seo_tags_deduplicated(self, seo: GhibliSEO) -> None:
        """generate_tags() contains no duplicate entries."""
        tags = seo.generate_tags(topic="test", extra_keywords=["Ghibli ASMR", "cozy ASMR"])
        assert len(tags) == len(set(tags))

    def test_ghibli_seo_description_contains_ghibli(self, seo: GhibliSEO) -> None:
        """generate_description() contains 'Ghibli'."""
        desc = seo.generate_description(topic="morning in the village")
        assert "Ghibli" in desc

    def test_ghibli_seo_description_contains_asmr(self, seo: GhibliSEO) -> None:
        """generate_description() contains 'ASMR'."""
        desc = seo.generate_description(topic="morning in the village")
        assert "ASMR" in desc

    def test_ghibli_seo_description_two_paragraphs(self, seo: GhibliSEO) -> None:
        """generate_description() contains at least one paragraph break."""
        desc = seo.generate_description(topic="test topic")
        assert "\n\n" in desc

    def test_seo_score_range(self, seo: GhibliSEO) -> None:
        """score_title() always returns a value in [0, 1]."""
        titles = [
            "Cozy Ghibli ASMR — relaxing no talking village 🌿",
            "x",
            "A" * 200,
            "",
        ]
        for title in titles:
            score = seo.score_title(title)
            assert 0.0 <= score <= 1.0, f"score {score} out of range for title: {title!r}"

    def test_seo_score_good_title(self, seo: GhibliSEO) -> None:
        """A title with all MUST_HAVE keywords scores > 0.5."""
        title = "Cozy Ghibli ASMR — relaxing no talking village sounds 🌿"
        assert seo.score_title(title) > 0.5

    def test_seo_score_empty_title(self, seo: GhibliSEO) -> None:
        """Empty title scores 0.0."""
        assert seo.score_title("") == 0.0

    def test_must_have_keywords_class_constant(self) -> None:
        """MUST_HAVE_KEYWORDS class constant contains expected entries."""
        assert "ASMR" in GhibliSEO.MUST_HAVE_KEYWORDS
        assert "Ghibli" in GhibliSEO.MUST_HAVE_KEYWORDS
        assert "cozy" in GhibliSEO.MUST_HAVE_KEYWORDS
