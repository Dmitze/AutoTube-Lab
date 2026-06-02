"""Unit tests for ABTester (statistical comparison of variants).

Roadmap tasks: T-356 through T-359 (EPIC 5.4)
"""

import pytest
from unittest.mock import MagicMock
from ytaimbot_ml.feedback.ab_tester import ABTester
from ytaimbot_ml.schemas import ABTestResult

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def tester(mock_storage):
    return ABTester(storage=mock_storage)

def test_analyze_too_small_sample(tester):
    """Test that sample size < 1000 returns inconclusive (T-357)."""
    tester.record_impression("v1", "a")
    tester.record_click("v1", "a")
    tester.record_impression("v1", "b")
    
    result = tester.analyze("v1")
    
    assert result.winner == "inconclusive"
    assert result.significant == False

def test_analyze_significant_winner(tester):
    """Test that significant winner is correctly identified (T-358)."""
    # Variant A: 100 clicks / 1000 impressions (10% CTR)
    for _ in range(100): tester.record_click("v1", "a")
    for _ in range(900): tester.record_impression("v1", "a")
    tester._counts["v1"]["a"]["impressions"] = 1000 # Correcting for record_click calls
    
    # Variant B: 50 clicks / 1000 impressions (5% CTR)
    for _ in range(50): tester.record_click("v1", "b")
    for _ in range(950): tester.record_impression("v1", "b")
    tester._counts["v1"]["b"]["impressions"] = 1000
    
    result = tester.analyze("v1")
    
    assert result.winner == "a"
    assert result.significant == True
    assert result.p_value < 0.05

def test_analyze_not_significant(tester):
    """Test that small differences return inconclusive (T-353)."""
    # Variant A: 100 clicks / 1000 impressions
    tester._counts["v1"] = {
        "a": {"clicks": 100, "impressions": 1000},
        "b": {"clicks": 105, "impressions": 1000}, # Only 5 click difference
    }
    
    result = tester.analyze("v1")
    
    assert result.winner == "inconclusive"
    assert result.significant == False
    assert result.p_value >= 0.05
