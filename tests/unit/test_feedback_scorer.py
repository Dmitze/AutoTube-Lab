"""Unit tests for FeedbackScorer (EMA niche weights).

Roadmap tasks: T-345 through T-348 (EPIC 5.3)
"""

import pytest
from unittest.mock import MagicMock
from ytaimbot_ml.feedback.scorer import FeedbackScorer
from ytaimbot_ml.schemas import MetricsSnapshot

@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.load_niche_weights.return_value = {"tech": 1.0}
    return storage

@pytest.fixture
def scorer(mock_storage):
    return FeedbackScorer(storage=mock_storage, alpha=0.3)

def test_update_ema(scorer, mock_storage):
    """Test that EMA update moves weight towards signal (T-346)."""
    # Current weight = 1.0, alpha = 0.3
    # Metrics with high views -> signal > 1.0
    metrics = MetricsSnapshot(video_id="v1", views=2000, ctr=0.1) # signal = (2.0 + 2.0) / 2 = 2.0
    
    new_weight = scorer.update("tech", metrics)
    
    # Expected: 0.3 * 2.0 + 0.7 * 1.0 = 0.6 + 0.7 = 1.3
    # BUT safety bounds clip it to 1.0 * 1.2 = 1.2
    assert new_weight == pytest.approx(1.2)
    assert mock_storage.save_niche_weights.called

def test_safety_bounds(scorer):
    """Test that weights don't jump more than 20% (T-347)."""
    metrics_viral = MetricsSnapshot(video_id="v1", views=100000, ctr=0.5)
    
    # Starting at 1.0
    w1 = scorer.update("viral", metrics_viral)
    assert w1 == pytest.approx(1.2) # clipped from 1.3+
    
    # Second update from 1.2
    w2 = scorer.update("viral", metrics_viral)
    assert w2 == pytest.approx(1.44) # 1.2 * 1.2

def test_get_weights(scorer):
    """Test retrieving all weights (T-343)."""
    scorer.update("n1", MetricsSnapshot(video_id="v1", views=100))
    scorer.update("n2", MetricsSnapshot(video_id="v2", views=5000))
    
    weights = scorer.get_weights()
    assert "n1" in weights
    assert "n2" in weights
    assert weights["n2"] > weights["n1"]
