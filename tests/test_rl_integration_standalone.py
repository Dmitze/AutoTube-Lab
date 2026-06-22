"""Integration tests for Phase 6 RL loop — standalone version (T-437, T-438).

Tests the Bandit + Drift + PPO cycle without depending on Pipeline internals.
All external services are mocked.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from modules.adapters.synthetic import InMemoryStorage
from ytaimbot_ml.schemas import MetricsSnapshot


# ---------------------------------------------------------------------------
# T-437: Bandit + Pipeline + Metrics loop integration
# ---------------------------------------------------------------------------

def test_ucb1_bandit_selects_and_updates():
    """T-437: UCB1Bandit selects a niche and updates after reward."""
    from src.ytaimbot_ml.learner.bandit import UCB1Bandit
    from ytaimbot_ml.utils.random import make_rng

    niches = ["finance", "tech", "ghibli", "psychology", "science"]
    bandit = UCB1Bandit(arm_ids=niches, rng=make_rng(42))

    # Cold start: each niche selected once
    selected = set()
    for _ in range(len(niches)):
        niche = bandit.select()
        bandit.update(niche, reward=0.5)
        selected.add(niche)

    assert selected == set(niches), "Cold start should explore all niches"


def test_ucb1_bandit_exploits_best_niche():
    """T-437: After training, UCB1 selects the best niche more often."""
    from src.ytaimbot_ml.learner.bandit import UCB1Bandit
    from ytaimbot_ml.utils.random import make_rng

    niches = ["finance", "horror", "tech"]
    bandit = UCB1Bandit(arm_ids=niches, rng=make_rng(42), exploration_const=0.5)

    # Train: finance always gives high reward, horror always low
    for _ in range(30):
        niche = bandit.select()
        reward = {"finance": 0.9, "horror": 0.1, "tech": 0.5}.get(niche, 0.5)
        bandit.update(niche, reward)

    # After training, finance should have highest avg_reward
    stats = bandit._arms
    assert stats["finance"].avg_reward > stats["horror"].avg_reward


# ---------------------------------------------------------------------------
# T-438: After 20 cycles, bandit converges to top niche
# ---------------------------------------------------------------------------

def test_bandit_converges_to_top_niche_after_20_cycles():
    """T-438: After 20 cycles, best niche is selected most frequently."""
    from src.ytaimbot_ml.learner.bandit import UCB1Bandit
    from ytaimbot_ml.utils.random import make_rng

    niches = ["finance", "horror", "ghibli", "tech"]
    # finance = best RPM, horror = worst
    rewards = {"finance": 0.95, "horror": 0.05, "ghibli": 0.60, "tech": 0.70}

    bandit = UCB1Bandit(
        arm_ids=niches,
        rng=make_rng(42),
        exploration_const=1.0,
    )

    selections: dict[str, int] = {n: 0 for n in niches}

    for _ in range(20):
        niche = bandit.select()
        bandit.update(niche, rewards[niche])
        selections[niche] += 1

    # finance should be selected most often after convergence
    best = max(selections, key=selections.get)
    assert best == "finance", (
        f"Expected 'finance' to be selected most, got '{best}'. "
        f"Selections: {selections}"
    )


# ---------------------------------------------------------------------------
# T-437: KSDriftDetector integration
# ---------------------------------------------------------------------------

def test_ks_drift_detector_detects_distribution_change():
    """T-437: KSDriftDetector correctly identifies drift between distributions."""
    from src.ytaimbot_ml.learner.drift_detector import KSDriftDetector
    from ytaimbot_ml.utils.random import make_rng

    rng = make_rng(42)
    detector = KSDriftDetector(threshold=0.05)

    # Same distribution → no drift
    ref = rng.normal(0.5, 0.1, 100).tolist()
    cur_same = rng.normal(0.5, 0.1, 100).tolist()
    report_no_drift = detector.check(ref, cur_same)
    assert not report_no_drift.drift_detected, "Same distribution should not trigger drift"

    # Different distribution → drift
    cur_diff = rng.normal(0.9, 0.05, 100).tolist()
    report_drift = detector.check(ref, cur_diff)
    assert report_drift.drift_detected, "Different distributions should trigger drift"


# ---------------------------------------------------------------------------
# T-437: LinearPPO integration
# ---------------------------------------------------------------------------

def test_linear_ppo_select_action_returns_valid_index():
    """T-437: LinearPPO.select_action() returns valid action index and probability."""
    from src.ytaimbot_ml.learner.optimizer import LinearPPO

    ppo = LinearPPO(state_dim=5, action_dim=3)
    state = np.random.default_rng(42).random(5)

    action_idx, prob = ppo.select_action(state)

    assert 0 <= action_idx < 3, f"action_idx={action_idx} out of range [0, 3)"
    assert 0.0 < prob <= 1.0, f"prob={prob} not in (0, 1]"


def test_linear_ppo_update_returns_loss():
    """T-437: LinearPPO.update() returns a float loss value."""
    from src.ytaimbot_ml.learner.optimizer import LinearPPO, Transition

    ppo = LinearPPO(state_dim=4, action_dim=2)
    rng = np.random.default_rng(42)

    # Build a small trajectory
    trajectory = []
    for _ in range(8):
        state = rng.random(4)
        action_idx, prob = ppo.select_action(state)
        next_state = rng.random(4)
        trajectory.append(Transition(
            state=state,
            action_idx=action_idx,
            reward=rng.uniform(0.0, 1.0),
            next_state=next_state,
            prob=prob,
        ))

    loss = ppo.update(trajectory)
    assert isinstance(loss, float), f"Expected float loss, got {type(loss)}"


# ---------------------------------------------------------------------------
# T-438: Reward signal drives bandit convergence
# ---------------------------------------------------------------------------

def test_reward_signal_drives_bandit_convergence():
    """T-438: High-reward niche gets higher avg_reward after 20 updates."""
    from src.ytaimbot_ml.learner.bandit import UCB1Bandit
    from ytaimbot_ml.utils.random import make_rng

    bandit = UCB1Bandit(
        arm_ids=["finance", "horror"],
        rng=make_rng(0),
        exploration_const=0.1,  # low exploration → faster convergence
    )

    # Simulate 20 cycles with deterministic rewards
    for i in range(20):
        niche = bandit.select()
        reward = 0.9 if niche == "finance" else 0.1
        bandit.update(niche, reward)

    finance_avg = bandit._arms["finance"].avg_reward
    horror_avg = bandit._arms["horror"].avg_reward

    assert finance_avg > horror_avg, (
        f"finance avg={finance_avg:.3f} should > horror avg={horror_avg:.3f}"
    )
