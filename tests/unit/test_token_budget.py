"""Unit tests for TokenBudget (Phase 2, T-100)."""

from ytaimbot_ml.content.token_budget import TokenBudget


STANDARD_SECTIONS = ["hook", "intro", "body_1", "body_2", "body_3", "cta"]


class TestTokenBudget:
    def test_allocate_returns_all_sections(self):
        """All input sections appear in output dict."""
        budget = TokenBudget(total_tokens=2048)
        alloc = budget.allocate(STANDARD_SECTIONS)
        assert set(alloc.keys()) == set(STANDARD_SECTIONS)

    def test_total_does_not_exceed_budget(self):
        """sum(allocations.values()) <= total_tokens."""
        budget = TokenBudget(total_tokens=1000)
        alloc = budget.allocate(STANDARD_SECTIONS)
        assert sum(alloc.values()) <= 1000

    def test_hook_gets_more_than_intro(self):
        """hook budget > intro budget (priority weighting)."""
        budget = TokenBudget(total_tokens=2048)
        alloc = budget.allocate(STANDARD_SECTIONS)
        assert alloc["hook"] > alloc["intro"]

    def test_cta_gets_more_than_body(self):
        """cta budget > each body section budget (cta weight=1.2 > body=1.0)."""
        budget = TokenBudget(total_tokens=2048)
        alloc = budget.allocate(STANDARD_SECTIONS)
        assert alloc["cta"] > alloc["body_1"]

    def test_empty_sections_returns_empty(self):
        """Empty input → empty allocation dict."""
        budget = TokenBudget(total_tokens=2048)
        assert budget.allocate([]) == {}

    def test_single_section_gets_most_of_budget(self):
        """Single section → gets nearly entire budget."""
        budget = TokenBudget(total_tokens=500)
        alloc = budget.allocate(["hook"])
        assert alloc["hook"] <= 500
        assert alloc["hook"] >= 64  # at least MIN_TOKENS

    def test_all_values_positive(self):
        """All allocated budgets are positive integers."""
        budget = TokenBudget(total_tokens=200)
        alloc = budget.allocate(STANDARD_SECTIONS)
        assert all(v > 0 for v in alloc.values())

    def test_deterministic(self):
        """Same input always produces same output."""
        budget = TokenBudget(total_tokens=2048)
        alloc1 = budget.allocate(STANDARD_SECTIONS)
        alloc2 = budget.allocate(STANDARD_SECTIONS)
        assert alloc1 == alloc2

    def test_custom_weights(self):
        """Custom weights override defaults."""
        custom = {"a": 2.0, "b": 1.0}
        budget = TokenBudget(total_tokens=300, weights=custom)
        alloc = budget.allocate(["a", "b"])
        assert alloc["a"] > alloc["b"]

    def test_estimate_words(self):
        """estimate_words(100) == 75."""
        budget = TokenBudget()
        assert budget.estimate_words(100) == 75

    def test_unknown_section_uses_fallback_weight(self):
        """Unknown section name uses default body weight (1.0)."""
        budget = TokenBudget(total_tokens=300)
        alloc = budget.allocate(["unknown_section"])
        assert alloc["unknown_section"] > 0

