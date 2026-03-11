"""Unit tests for UCB1Bandit (Phase 6, T-500).

Test cases:
  test_select_unplayed_arm_first       : unplayed arms selected first
  test_update_changes_mean             : reward updates empirical mean
  test_regret_sublinear                : cumulative regret < C√(kN ln N)
  test_deterministic_tiebreaking       : same seed → same selection on tie
  test_reset_clears_state              : reset() → all zeros
  test_exploit_after_enough_trials     : exploits best arm after convergence

Status: 🔲 Pending — implement after T-500
"""
import pytest

# TODO: import UCB1Bandit after T-500 is implemented
# from ytaimbot_ml.rl.ucb1_bandit import UCB1Bandit


@pytest.mark.skip(reason="T-500 not implemented yet")
def test_select_unplayed_arm_first():
    """All arms played once before exploitation begins."""
    pass


@pytest.mark.skip(reason="T-500 not implemented yet")
def test_update_changes_mean():
    """update(arm=0, reward=1.0) increases x̄_0."""
    pass


@pytest.mark.skip(reason="T-500 not implemented yet")
def test_regret_sublinear():
    """Cumulative regret grows sub-linearly over 1000 trials."""
    pass


@pytest.mark.skip(reason="T-500 not implemented yet")
def test_deterministic_tiebreaking():
    """Same seed → same arm on tie."""
    pass


@pytest.mark.skip(reason="T-500 not implemented yet")
def test_reset_clears_state():
    """After reset(), counts and values all zero."""
    pass
