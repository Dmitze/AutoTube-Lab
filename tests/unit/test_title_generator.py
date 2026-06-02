"""Unit tests for TitleGenerator (CTR-optimized YouTube titles).

Roadmap tasks: T-220 through T-225 (EPIC 3.5)
"""

import pytest
from ytaimbot_ml.seo.title_generator import TitleGenerator
from ytaimbot_ml.schemas import ContentPlan

@pytest.fixture
def generator():
    return TitleGenerator()

def test_generate_variants_count(generator):
    """Test that generate_variants returns 3 unique variants (T-221)."""
    plan = ContentPlan(trend_id="t1", title="Python Tutorial", outline=[], keywords=["python"])
    variants = generator.generate_variants(plan, n=3)
    
    assert len(variants) == 3
    assert len(set(variants)) == 3

def test_validate_length(generator):
    """Test that each title is within 40–60 characters (T-222)."""
    long_title = "This is a very long title that should definitely be trimmed because it is way over 60 characters"
    plan = ContentPlan(trend_id="t1", title=long_title, outline=[], keywords=["python"])
    
    variants = generator.generate_variants(plan, n=3)
    
    for v in variants:
        assert len(v) <= 60
        # Should be at least 40 if the input was long enough
        assert len(v) >= 40

def test_ctr_score_features(generator):
    """Test CTR scoring features (T-223)."""
    # High score: number + power word + question + optimal length
    high_score_title = "Secret: 5 Amazing Python Tips for Beginners?"
    # Low score: short, no number, no power word
    low_score_title = "Python basic"
    
    score_high = generator.ctr_score(high_score_title)
    score_low = generator.ctr_score(low_score_title)
    
    assert score_high > score_low
    assert score_high >= 0.6

def test_select_best(generator):
    """Test that select_best chooses the highest scoring variant (T-217)."""
    variants = [
        "Python basic",                        # low score
        "5 Amazing Python Tips",              # high score
        "How to use Python in 2026",          # medium score
    ]
    
    best = generator.select_best(variants)
    
    assert best == "5 Amazing Python Tips"

def test_determinism(generator):
    """Test that same input leads to same variants (T-224)."""
    plan = ContentPlan(trend_id="t1", title="Python Tutorial", outline=[], keywords=["python"])
    
    res1 = generator.generate_variants(plan)
    res2 = generator.generate_variants(plan)
    
    assert res1 == res2

def test_keyword_presence(generator):
    """Test that seed keyword is present in variants (T-225)."""
    plan = ContentPlan(trend_id="t1", title="Test", outline=[], keywords=["automation"])
    
    variants = generator.generate_variants(plan)
    
    # Check if 'automation' is present in at least 2 out of 3 variants
    count = sum(1 for v in variants if "automation" in v.lower())
    assert count >= 2
