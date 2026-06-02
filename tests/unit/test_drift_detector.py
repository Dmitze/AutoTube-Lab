"""Unit tests for KSDriftDetector (distribution drift).

Roadmap tasks: T-403 through T-407 (EPIC 6.2)
"""

import pytest
import numpy as np
from ytaimbot_ml.learner.drift_detector import KSDriftDetector

@pytest.fixture
def detector():
    return KSDriftDetector(threshold=0.05)

def test_check_no_drift(detector):
    """Test that identical distributions pass (T-404)."""
    rng = np.random.default_rng(42)
    ref = rng.normal(0, 1, 1000).tolist()
    cur = rng.normal(0, 1, 1000).tolist()
    
    report = detector.check(ref, cur)
    
    assert report.drift_detected == False
    assert report.p_value > 0.05

def test_check_drift_detected(detector):
    """Test that different distributions are detected (T-405)."""
    rng = np.random.default_rng(42)
    ref = rng.normal(0, 1, 1000).tolist()
    cur = rng.normal(5, 1, 1000).tolist() # Shifted mean
    
    report = detector.check(ref, cur)
    
    assert report.drift_detected == True
    assert report.p_value < 0.05
    assert report.action == "reset_bandit"

def test_reservoir_sample(detector):
    """Test reservoir sampling logic (T-406)."""
    rng = np.random.default_rng(42)
    stream = list(range(1000))
    k = 100
    
    sample = detector.reservoir_sample(stream, k, rng)
    
    assert len(sample) == k
    assert all(0 <= x < 1000 for x in sample)
    # Check that it's not just the first 100 elements
    assert sample != stream[:k]
