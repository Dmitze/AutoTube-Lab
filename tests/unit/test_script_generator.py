"""Unit tests for ScriptGenerator (Phase 2, T-124–T-135).

All LLM calls are replaced by MockLLMAdapter — no real API required.
"""
from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock

from ytaimbot_ml.content.script_generator import (
    SECTION_ORDER,
    MIN_TOTAL_WORDS,
    ScriptGenerator,
)
from ytaimbot_ml.content.token_budget import TokenBudget
from ytaimbot_ml.schemas import ContentPlan, Script, ScriptSection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_llm(words_per_call: int = 100) -> MagicMock:
    """Return a mock LLMAdapter that generates N words per call."""
    mock = MagicMock()
    mock.generate.side_effect = lambda prompt, max_tokens=512: " ".join(
        ["word"] * words_per_call
    )
    return mock


def _make_plan(keywords: list[str] | None = None) -> ContentPlan:
    return ContentPlan(
        trend_id="trend_test_001",
        title="How Python Changed My Life",
        outline=["Point 1: History", "Point 2: Use cases", "Point 3: Future"],
        keywords=keywords or ["python", "programming", "tutorial"],
    )


def _make_rng(seed: int = 42) -> np.random.Generator:
    return np.random.default_rng(seed)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestScriptGenerator:
    def test_generate_returns_script_instance(self):
        """generate() returns a Script dataclass instance."""
        llm = _make_mock_llm(100)
        gen = ScriptGenerator(llm=llm, language="en")
        script = gen.generate(_make_plan(), _make_rng())
        assert isinstance(script, Script)

    def test_generate_has_all_sections(self):
        """Script contains all 6 sections in order."""
        llm = _make_mock_llm(100)
        gen = ScriptGenerator(llm=llm, language="en")
        script = gen.generate(_make_plan(), _make_rng())
        section_names = [s.name for s in script.sections]
        assert section_names == SECTION_ORDER

    def test_generate_calls_llm_six_times(self):
        """LLM is called once per section (6 total)."""
        llm = _make_mock_llm(100)
        gen = ScriptGenerator(llm=llm, language="en")
        gen.generate(_make_plan(), _make_rng())
        assert llm.generate.call_count == 6

    def test_generate_passes_max_tokens_from_budget(self):
        """LLM generate() is called with max_tokens from TokenBudget."""
        llm = _make_mock_llm(100)
        budget = TokenBudget(total_tokens=600)
        gen = ScriptGenerator(llm=llm, budget=budget, language="en")
        gen.generate(_make_plan(), _make_rng())
        calls = llm.generate.call_args_list
        for call in calls:
            _, kwargs = call
            assert "max_tokens" in kwargs
            assert kwargs["max_tokens"] >= 64  # at least MIN_TOKENS

    def test_total_words_meets_minimum(self):
        """Script total_words >= MIN_TOTAL_WORDS (500)."""
        words_per_section = (MIN_TOTAL_WORDS // len(SECTION_ORDER)) + 10
        llm = _make_mock_llm(words_per_section)
        gen = ScriptGenerator(llm=llm, language="en")
        script = gen.generate(_make_plan(), _make_rng())
        assert script.total_words >= MIN_TOTAL_WORDS

    def test_validate_raises_on_short_script(self):
        """ValueError raised if script < 500 words."""
        llm = _make_mock_llm(5)  # only 5 words per section → ~30 total
        gen = ScriptGenerator(llm=llm, language="en")
        with pytest.raises(ValueError, match="Script too short"):
            gen.generate(_make_plan(), _make_rng())

    def test_plan_id_matches_trend_id(self):
        """Script.plan_id equals ContentPlan.trend_id."""
        llm = _make_mock_llm(100)
        gen = ScriptGenerator(llm=llm, language="en")
        plan = _make_plan()
        script = gen.generate(plan, _make_rng())
        assert script.plan_id == plan.trend_id

    def test_language_stored_in_script(self):
        """Script.language matches generator language setting."""
        llm = _make_mock_llm(100)
        gen = ScriptGenerator(llm=llm, language="uk")
        script = gen.generate(_make_plan(), _make_rng())
        assert script.language == "uk"

    def test_section_text_not_empty(self):
        """Each section has non-empty text."""
        llm = _make_mock_llm(100)
        gen = ScriptGenerator(llm=llm, language="en")
        script = gen.generate(_make_plan(), _make_rng())
        for section in script.sections:
            assert len(section.text) > 0

    def test_deterministic_with_same_seed(self):
        """Same seed + same plan → same section structure."""
        llm1 = _make_mock_llm(100)
        llm2 = _make_mock_llm(100)
        gen1 = ScriptGenerator(llm=llm1, language="en")
        gen2 = ScriptGenerator(llm=llm2, language="en")
        plan = _make_plan()
        s1 = gen1.generate(plan, _make_rng(42))
        s2 = gen2.generate(plan, _make_rng(42))
        assert [sec.name for sec in s1.sections] == [sec.name for sec in s2.sections]

    def test_keywords_injected_in_hook(self):
        """Keywords missing from LLM output are appended to section text."""
        llm = MagicMock()
        # LLM returns text with NO keywords
        llm.generate.side_effect = lambda prompt, max_tokens=512: " ".join(
            ["generic"] * 100
        )
        gen = ScriptGenerator(llm=llm, language="en")
        plan = _make_plan(keywords=["rare_keyword_xyz"])
        script = gen.generate(plan, _make_rng())
        hook = next(s for s in script.sections if s.name == "hook")
        assert "rare_keyword_xyz" in hook.text

    def test_inject_keywords_noop_when_present(self):
        """_inject_keywords does not duplicate already-present keywords."""
        result = ScriptGenerator._inject_keywords("python is great", ["python"])
        assert result.count("python") == 1

    def test_inject_keywords_appends_missing(self):
        """_inject_keywords appends missing keywords in parentheses."""
        result = ScriptGenerator._inject_keywords("hello world", ["python"])
        assert "python" in result

    def test_inject_keywords_empty_list(self):
        """_inject_keywords returns text unchanged with empty keywords."""
        text = "unchanged text"
        assert ScriptGenerator._inject_keywords(text, []) == text

    def test_build_prompt_contains_title(self):
        """_build_prompt includes plan title in the prompt string."""
        llm = _make_mock_llm(100)
        gen = ScriptGenerator(llm=llm, language="en")
        plan = _make_plan()
        prompt = gen._build_prompt("hook", plan, [])
        assert plan.title in prompt

    def test_uk_prompt_in_ukrainian(self):
        """Ukrainian language prompts contain Ukrainian text."""
        llm = _make_mock_llm(100)
        gen = ScriptGenerator(llm=llm, language="uk")
        plan = _make_plan()
        prompt = gen._build_prompt("hook", plan, [])
        assert "сценарист" in prompt or "YouTube" in prompt

    def test_section_word_count_auto_computed(self):
        """ScriptSection.word_count is auto-computed from text."""
        section = ScriptSection(name="hook", text="one two three four five")
        assert section.word_count == 5

    def test_section_token_estimate_auto_computed(self):
        """ScriptSection.token_estimate ≈ word_count × 1.3."""
        section = ScriptSection(name="hook", text="one two three four five")
        assert section.token_estimate == int(5 * 1.3)

    def test_script_total_words_property(self):
        """Script.total_words sums all section word counts."""
        sections = [
            ScriptSection(name="hook", text="a " * 100),
            ScriptSection(name="cta", text="b " * 50),
        ]
        script = Script(plan_id="x", sections=sections)
        assert script.total_words == 150

    def test_script_total_tokens_property(self):
        """Script.total_tokens sums all section token estimates."""
        s1 = ScriptSection(name="hook", text="word " * 100)
        s2 = ScriptSection(name="cta", text="word " * 50)
        script = Script(plan_id="x", sections=[s1, s2])
        assert script.total_tokens == s1.token_estimate + s2.token_estimate
