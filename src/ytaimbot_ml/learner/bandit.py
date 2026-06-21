"""Phase 6 — Multi-Armed Bandits for Niche Selection.

Roadmap tasks: T-381 through T-395 (EPIC 6.1 Bandit Algorithm)

Algorithm
---------
UCB1 (Upper Confidence Bound):
    Score = avg_reward + sqrt(2 * ln(total_pulls) / n_pulls)
    Regret: O(sqrt(K * N * ln N))

Softmax (Boltzmann Exploration):
    P(arm_i) = exp(avg_reward_i / temp) / sum(exp(avg_reward_j / temp))
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from ytaimbot_ml.utils.random import make_rng

logger = logging.getLogger(__name__)


@dataclass
class ArmStats:
    """Statistics for a single bandit arm (niche)."""
    arm_id: str
    n_pulls: int = 0
    total_reward: float = 0.0
    last_reward: float = 0.0

    @property
    def avg_reward(self) -> float:
        """Mean reward for this arm."""
        return self.total_reward / self.n_pulls if self.n_pulls > 0 else 0.0


class UCB1Bandit:
    """UCB1 bandit for optimal niche selection."""

    DEFAULT_NICHE_ARMS: list[str] = [
        "tech_tutorials",
        "finance_tips",
        "health_wellness",
        "gaming",
        "cooking",
    ]

    def __init__(
        self,
        arm_ids: List[str],
        rng: Optional[np.random.Generator] = None,
        exploration_const: float = 2.0,
    ) -> None:
        self.arm_ids = arm_ids
        self._rng = rng or make_rng(42)
        self.C = exploration_const
        self._arms = {aid: ArmStats(arm_id=aid) for aid in arm_ids}
        self._total_pulls = 0

    def select(self) -> str:
        """Select an arm using UCB1 formula.  O(k)."""
        # 1. Cold start: try each arm once
        for aid in self.arm_ids:
            if self._arms[aid].n_pulls == 0:
                return aid

        # 2. UCB1 Score
        log_total = math.log(self._total_pulls)
        best_aid = self.arm_ids[0]
        max_score = -1.0

        for aid in self.arm_ids:
            arm = self._arms[aid]
            score = arm.avg_reward + self.C * math.sqrt(log_total / arm.n_pulls)
            if score > max_score:
                max_score = score
                best_aid = aid
        
        return best_aid

    def update(self, arm_id: str, reward: float) -> None:
        """Update arm stats with observed reward [0, 1].  O(1)."""
        if arm_id not in self._arms:
            return
        
        reward = float(np.clip(reward, 0.0, 1.0))
        arm = self._arms[arm_id]
        arm.n_pulls += 1
        arm.total_reward += reward
        arm.last_reward = reward
        self._total_pulls += 1
        
        logger.debug("Bandit: updated %s (avg=%.2f)", arm_id, arm.avg_reward)

    def get_stats(self) -> Dict[str, ArmStats]:
        return dict(self._arms)


class SoftmaxBandit:
    """Softmax (Boltzmann) bandit for niche selection."""

    def __init__(
        self,
        arm_ids: List[str],
        rng: Optional[np.random.Generator] = None,
        temperature: float = 0.1,
    ) -> None:
        self.arm_ids = arm_ids
        self._rng = rng or make_rng(42)
        self.temp = temperature
        self._arms = {aid: ArmStats(arm_id=aid) for aid in arm_ids}
        self._total_pulls = 0

    def select(self) -> str:
        """Select an arm using Softmax distribution.  O(k)."""
        avg_rewards = np.array([self._arms[aid].avg_reward for aid in self.arm_ids])
        
        # Softmax with temperature
        exp_rewards = np.exp(avg_rewards / self.temp)
        probs = exp_rewards / np.sum(exp_rewards)
        
        return self._rng.choice(self.arm_ids, p=probs)

    def update(self, arm_id: str, reward: float) -> None:
        """O(1)."""
        if arm_id not in self._arms:
            return
        reward = float(np.clip(reward, 0.0, 1.0))
        arm = self._arms[arm_id]
        arm.n_pulls += 1
        arm.total_reward += reward
        arm.last_reward = reward
        self._total_pulls += 1
