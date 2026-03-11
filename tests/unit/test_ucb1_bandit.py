"""Unit tests for UCB1Bandit and RewardShaper (Phase 6, T-500).

Test cases:
  test_select_unplayed_arm_first       : unplayed arms selected first
  test_update_changes_mean             : reward updates empirical mean
  test_regret_sublinear                : cumulative regret < baseline
  test_deterministic_tiebreaking       : same seed → same selection on tie
  test_reset_clears_state              : reset() → all zeros
  test_exploit_after_enough_trials     : exploits best arm after convergence
  test_best_arm                        : best_arm returns highest avg_reward
  test_serialisation_round_trip        : to_dict / from_dict
  test_reward_shaper_bounds            : reward always in [0, 1]
  test_reward_shaper_at_target         : at-target metrics → reward ≈ 1.0
  test_reward_shaper_welford           : running mean/variance update
  test_unknown_arm_raises              : update with unknown arm raises KeyError
"""

import numpy as np
import pytest

from ytaimbot_ml.rl.ucb1_bandit import UCB1Bandit
from ytaimbot_ml.rl.reward_shaper import RewardShaper
from ytaimbot_ml.utils.random import make_rng


# ---------------------------------------------------------------------------
# UCB1Bandit tests
# ---------------------------------------------------------------------------


def test_select_unplayed_arm_first() -> None:
    """All arms are played exactly once before exploitation begins."""
    arms = ["ghibli", "finance", "ai_tech"]
    bandit = UCB1Bandit(arm_ids=arms, rng=make_rng(0))
    seen: list[str] = []
    for _ in arms:
        chosen = bandit.select()
        assert chosen not in seen, "Same arm selected twice during exploration."
        seen.append(chosen)
        bandit.update(chosen, reward=0.5)
    assert set(seen) == set(arms)


def test_update_changes_mean() -> None:
    """update(arm, reward) increments n_pulls and adjusts avg_reward."""
    bandit = UCB1Bandit(arm_ids=["a", "b"])
    bandit.update("a", reward=1.0)
    assert bandit.stats["a"].n_pulls == 1
    assert bandit.stats["a"].avg_reward == pytest.approx(1.0)
    assert bandit.stats["b"].n_pulls == 0


def test_regret_sublinear() -> None:
    """Bandit converges: cumulative reward in last quarter > first quarter."""
    rng = make_rng(42)
    arms = ["low", "mid", "high"]
    true_rewards = {"low": 0.2, "mid": 0.5, "high": 0.8}
    bandit = UCB1Bandit(arm_ids=arms, rng=rng)
    N = 300
    rewards: list[float] = []
    for _ in range(N):
        arm = bandit.select()
        r = true_rewards[arm] + float(rng.normal(0, 0.05))
        r = float(np.clip(r, 0.0, 1.0))
        bandit.update(arm, r)
        rewards.append(r)
    first_q = sum(rewards[:N // 4])
    last_q = sum(rewards[3 * N // 4:])
    assert last_q > first_q, "Expected higher reward in last quarter (exploitation)."


def test_deterministic_tiebreaking() -> None:
    """Same seed produces same arm when all arms are freshly reset."""
    arms = ["a", "b", "c"]
    b1 = UCB1Bandit(arm_ids=arms, rng=make_rng(7))
    b2 = UCB1Bandit(arm_ids=arms, rng=make_rng(7))
    for _ in range(20):
        arm1 = b1.select()
        arm2 = b2.select()
        assert arm1 == arm2
        b1.update(arm1, 0.5)
        b2.update(arm2, 0.5)


def test_reset_clears_state() -> None:
    """After reset(), all counts and rewards are zero."""
    bandit = UCB1Bandit(arm_ids=["a", "b", "c"])
    bandit.update("a", 0.9)
    bandit.update("b", 0.3)
    bandit.reset()
    for arm in bandit.stats.values():
        assert arm.n_pulls == 0
        assert arm.total_reward == 0.0
    assert bandit.total_pulls == 0


def test_exploit_after_enough_trials() -> None:
    """After many pulls the best arm is selected most often."""
    rng = make_rng(0)
    arms = ["bad", "good"]
    bandit = UCB1Bandit(arm_ids=arms, rng=rng)
    true_rewards = {"bad": 0.1, "good": 0.9}
    for _ in range(200):
        arm = bandit.select()
        bandit.update(arm, true_rewards[arm])
    counts = {arm_id: s.n_pulls for arm_id, s in bandit.stats.items()}
    assert counts["good"] > counts["bad"]


def test_best_arm() -> None:
    """best_arm() returns the arm with highest avg_reward."""
    bandit = UCB1Bandit(arm_ids=["a", "b", "c"])
    bandit.update("a", 0.2)
    bandit.update("b", 0.9)
    bandit.update("c", 0.5)
    assert bandit.best_arm() == "b"


def test_serialisation_round_trip() -> None:
    """to_dict / from_dict preserves full bandit state."""
    bandit = UCB1Bandit(arm_ids=["x", "y"])
    bandit.update("x", 0.6)
    bandit.update("y", 0.3)
    restored = UCB1Bandit.from_dict(bandit.to_dict())
    assert restored.stats["x"].n_pulls == 1
    assert restored.stats["x"].avg_reward == pytest.approx(0.6)
    assert restored.total_pulls == bandit.total_pulls


def test_unknown_arm_raises() -> None:
    """update with unknown arm_id raises KeyError."""
    bandit = UCB1Bandit(arm_ids=["a"])
    with pytest.raises(KeyError):
        bandit.update("nonexistent", 0.5)


def test_reward_clamped() -> None:
    """Rewards outside [0, 1] are silently clamped."""
    bandit = UCB1Bandit(arm_ids=["a"])
    bandit.update("a", reward=5.0)
    assert bandit.stats["a"].last_reward == pytest.approx(1.0)
    bandit.update("a", reward=-1.0)
    assert bandit.stats["a"].last_reward == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# RewardShaper tests
# ---------------------------------------------------------------------------


def test_reward_shaper_bounds() -> None:
    """Shaped reward is always in [0, 1] for arbitrary inputs."""
    shaper = RewardShaper()
    cases = [
        (0.0, 0.0, 0),
        (0.06, 0.70, 10_000),
        (0.20, 1.00, 1_000_000),
        (0.001, 0.01, 1),
    ]
    for ctr, ret, views in cases:
        r = shaper.shape(ctr=ctr, retention_30s=ret, views=views)
        assert 0.0 <= r <= 1.0, f"Out of bounds for ({ctr}, {ret}, {views}): {r}"


def test_reward_shaper_at_target() -> None:
    """Exactly on-target metrics produce reward ≈ 1.0."""
    shaper = RewardShaper()
    r = shaper.shape(
        ctr=RewardShaper.CTR_TARGET,
        retention_30s=RewardShaper.RETENTION_TARGET,
        views=RewardShaper.VIEWS_TARGET,
    )
    assert r == pytest.approx(1.0, abs=1e-6)


def test_reward_shaper_welford() -> None:
    """Running mean and variance update correctly."""
    shaper = RewardShaper()
    assert shaper.n_samples == 0
    assert shaper.mean == 0.0
    assert shaper.variance == 0.0

    rewards = [
        shaper.shape(ctr=0.06, retention_30s=0.70, views=5_000),
        shaper.shape(ctr=0.04, retention_30s=0.60, views=2_000),
        shaper.shape(ctr=0.08, retention_30s=0.75, views=8_000),
    ]
    assert shaper.n_samples == 3
    assert shaper.mean == pytest.approx(sum(rewards) / 3, abs=1e-9)
    expected_var = sum((r - shaper.mean) ** 2 for r in rewards) / 2
    assert shaper.variance == pytest.approx(expected_var, abs=1e-9)


def test_reward_shaper_ordering() -> None:
    """Better metrics produce higher reward than worse metrics."""
    shaper = RewardShaper()
    high = shaper.shape(ctr=0.10, retention_30s=0.90, views=50_000)
    shaper2 = RewardShaper()
    low = shaper2.shape(ctr=0.02, retention_30s=0.30, views=100)
    assert high > low
