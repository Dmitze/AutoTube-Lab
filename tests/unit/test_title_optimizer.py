"""Unit tests for TitleOptimizer (Phase 3, T-137–T-148)."""

from ytaimbot_ml.schemas import ContentPlan
from ytaimbot_ml.seo.title_optimizer import TitleOptimizer, TitleScore


class TestTitleScore:
    def test_total_in_range(self):
        """Score total is always in [0, 1]."""
        opt = TitleOptimizer()
        s = opt.score("How to Learn Python in 30 Days", ["python"])
        assert 0.0 <= s.total <= 1.0

    def test_number_detected(self):
        """Title with number gets contains_number=1.0."""
        opt = TitleOptimizer()
        s = opt.score("Top 10 Python Tips", ["python"])
        assert s.contains_number == 1.0

    def test_no_number(self):
        """Title without digits gets contains_number=0.0."""
        opt = TitleOptimizer()
        s = opt.score("Learn Python Today", ["python"])
        assert s.contains_number == 0.0

    def test_keyword_present(self):
        """Primary keyword in title → keyword_present=1.0."""
        opt = TitleOptimizer()
        s = opt.score("Python Tutorial for Beginners", ["python"])
        assert s.keyword_present == 1.0

    def test_keyword_absent(self):
        """Primary keyword NOT in title → keyword_present=0.0."""
        opt = TitleOptimizer()
        s = opt.score("Amazing Video Today", ["python"])
        assert s.keyword_present == 0.0

    def test_curiosity_question_mark(self):
        """Question mark triggers curiosity_gap=1.0."""
        opt = TitleOptimizer()
        s = opt.score("Why Python?", ["python"])
        assert s.curiosity_gap == 1.0

    def test_optimal_length_score(self):
        """Title of 50 chars gets full length_ok=1.0."""
        opt = TitleOptimizer()
        title = "Python Tutorial for Absolute Beginners 2026 Tips"  # 49 chars
        s = opt.score(title, ["python"])
        assert s.length_ok == 1.0

    def test_short_title_partial_length(self):
        """Very short title gets partial length_ok < 1.0."""
        opt = TitleOptimizer()
        s = opt.score("Python", ["python"])
        assert s.length_ok < 1.0

    def test_power_word_starts(self):
        """Title starting with 'How' → starts_power_word=1.0."""
        opt = TitleOptimizer()
        s = opt.score("How to Master Python", ["python"])
        assert s.starts_power_word == 1.0

    def test_score_is_dataclass(self):
        """score() returns TitleScore dataclass."""
        opt = TitleOptimizer()
        result = opt.score("Python guide", ["python"])
        assert isinstance(result, TitleScore)


class TestTitleOptimizer:
    def test_optimize_returns_string(self):
        """optimize() returns non-empty string."""
        opt = TitleOptimizer()
        result = opt.optimize("Python", ["python"])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_optimize_contains_keyword(self):
        """Optimized title contains the keyword."""
        opt = TitleOptimizer()
        result = opt.optimize("Python", ["python"])
        assert "python" in result.lower() or "Python" in result

    def test_optimize_deterministic(self):
        """Same keyword → same output (no randomness)."""
        opt = TitleOptimizer()
        r1 = opt.optimize("Python", ["python"])
        r2 = opt.optimize("Python", ["python"])
        assert r1 == r2

    def test_variants_returns_three_keys(self):
        """variants() returns dict with keys short/medium/long."""
        opt = TitleOptimizer()
        vs = opt.variants("Python", ["python"])
        assert set(vs.keys()) == {"short", "medium", "long"}

    def test_variants_all_non_empty(self):
        """All variant strings are non-empty."""
        opt = TitleOptimizer()
        vs = opt.variants("Python", ["python"])
        assert all(len(v) > 0 for v in vs.values())

    def test_keyword_density_correct(self):
        """keyword_density("Python Python tutorial", "python") ≈ 0.667."""
        opt = TitleOptimizer()
        d = opt.keyword_density("Python Python tutorial", "python")
        assert abs(d - 2/3) < 0.01

    def test_keyword_density_zero(self):
        """Keyword not in title → density = 0.0."""
        opt = TitleOptimizer()
        assert opt.keyword_density("Hello world", "python") == 0.0

    def test_keyword_density_empty_title(self):
        """Empty title → density = 0.0 (no division by zero)."""
        opt = TitleOptimizer()
        assert opt.keyword_density("", "python") == 0.0

    def test_optimize_from_plan(self):
        """optimize_from_plan() uses first keyword as primary."""
        opt = TitleOptimizer()
        plan = ContentPlan(
            trend_id="t1",
            title="Python basics",
            outline=[],
            keywords=["python", "programming"],
        )
        result = opt.optimize_from_plan(plan)
        assert "python" in result.lower() or "Python" in result

    def test_year_injected_in_templates(self):
        """Year parameter appears in at least one template."""
        opt = TitleOptimizer(year="2099")
        candidates = opt._generate_candidates("Python")
        has_year = any("2099" in c for c in candidates)
        assert has_year

    def test_generate_candidates_count(self):
        """Correct number of candidates matches template count."""
        from ytaimbot_ml.seo.title_optimizer import _TITLE_TEMPLATES
        opt = TitleOptimizer()
        candidates = opt._generate_candidates("Test")
        assert len(candidates) == len(_TITLE_TEMPLATES)

