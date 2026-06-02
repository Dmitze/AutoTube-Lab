"""Unit tests for UCB1Bandit and SoftmaxBandit.

Roadmap tasks: T-390 through T-395 (EPIC 6.1)
"""

import pytest
import numpy as np
from ytaimbot_ml.learner.bandit import UCB1Bandit, SoftmaxBandit

@pytest.fixture
def arms():
    return ["niche_a", "niche_b", "niche_c"]

def test_ucb1_cold_start(arms):
    """Test that each arm is tried once during cold start (T-392)."""
    bandit = UCB1Bandit(arm_ids=arms)
    
    selected = []
    for _ in range(3):
        selected.append(bandit.select())
        bandit.update(selected[-1], 0.5)
    
    assert set(selected) == set(arms)

def test_ucb1_best_arm_preference(arms):
    """Test that UCB1 eventually picks the best arm more often (T-391)."""
    bandit = UCB1Bandit(arm_ids=arms, exploration_const=1.0)
    
    # Simulate 100 pulls
    # niche_a is the best (0.9 reward), others are worse (0.1)
    for _ in range(100):
        aid = bandit.select()
        reward = 0.9 if aid == "niche_a" else 0.1
        bandit.update(aid, reward)
    
    stats = bandit.get_stats()
    assert stats["niche_a"].n_pulls > stats["niche_b"].n_pulls
    assert stats["niche_a"].n_pulls > stats["niche_c"].n_pulls

def test_softmax_bandit(arms):
    """Test basic Softmax selection."""
    bandit = SoftmaxBandit(arm_ids=arms, temperature=0.1)
    
    # niche_a is much better
    bandit.update("niche_a", 1.0)
    bandit.update("niche_b", 0.0)
    bandit.update("niche_c", 0.0)
    
    # Should pick niche_a with high probability
    selections = [bandit.select() for _ in range(50)]
    assert selections.count("niche_a") > 40

def test_bandit_determinism(arms):
    """Test that seed leads to same sequence (T-394)."""
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)
    
    b1 = UCB1Bandit(arm_ids=arms, rng=rng1)
    b2 = UCB1Bandit(arm_ids=arms, rng=rng2)
    
    # After cold start, next selection should be deterministic
    for _ in range(3):
        b1.update(b1.select(), 0.5)
        b2.update(b2.select(), 0.5)
        
    assert b1.select() == b2.select()
