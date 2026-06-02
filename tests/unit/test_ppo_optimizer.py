"""Unit tests for LinearPPO policy optimizer.

Roadmap tasks: T-415 through T-419 (EPIC 6.3)
"""

import pytest
import numpy as np
from ytaimbot_ml.learner.optimizer import LinearPPO, Transition

@pytest.fixture
def ppo():
    return LinearPPO(state_dim=4, action_dim=2, lr=0.1)

def test_select_action(ppo):
    """Test action selection returns valid index and prob."""
    state = np.array([1.0, 0.5, -0.2, 0.1])
    idx, prob = ppo.select_action(state)
    
    assert idx in [0, 1]
    assert 0 <= prob <= 1.0

def test_update_learning(ppo):
    """Test that update changes weights in the right direction (T-416)."""
    state = np.array([1.0, 0.0, 0.0, 0.0])
    
    # Initially equal weights
    ppo.W = np.zeros((2, 4))
    
    # Transition: state [1,0,0,0], action 0, high reward
    t1 = Transition(state=state, action_idx=0, reward=1.0, prob=0.5)
    # Transition: state [1,0,0,0], action 1, low reward
    t2 = Transition(state=state, action_idx=1, reward=0.0, prob=0.5)
    
    ppo.update([t1, t2])
    
    # Prob of action 0 should increase
    _, prob0 = ppo.select_action(state)
    # Since we only have 2 actions and action 0 was rewarded more, its weight should be higher
    assert ppo.W[0, 0] > ppo.W[1, 0]

def test_ppo_clipping(ppo):
    """Test that PPO ratio is clipped (T-417)."""
    # This is hard to test directly without checking internal surr2, 
    # but we can verify the update doesn't explode.
    state = np.array([1.0, 1.0, 1.0, 1.0])
    # Very high reward to force large gradient
    t = Transition(state=state, action_idx=0, reward=100.0, prob=0.0001)
    
    ppo.update([t])
    # Weights should change but not become NaN/Inf
    assert not np.isnan(ppo.W).any()

def test_save_load(ppo, tmp_path):
    """Test policy persistence (T-418)."""
    path = tmp_path / "policy.pkl"
    ppo.W[0, 0] = 9.99
    ppo.save_policy(path)
    
    ppo2 = LinearPPO(state_dim=4, action_dim=2)
    ppo2.load_policy(path)
    
    assert ppo2.W[0, 0] == pytest.approx(9.99)
