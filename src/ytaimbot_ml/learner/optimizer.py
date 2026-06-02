"""Phase 6 — LinearPPO: lightweight policy optimization for content parameters.

Roadmap tasks: T-408 through T-419 (EPIC 6.3 PPO Policy Optimizer)
Dependencies:  numpy

Algorithm
---------
Linear Policy:
    π(a|s) = softmax(W @ s + b)
    Value V(s) = v_W @ s + v_b

PPO Clip (T-413):
    Loss = min(ratio * advantage, clip(ratio, 1-eps, 1+eps) * advantage)
    eps = 0.2
"""

from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Transition:
    """A single RL transition (s, a, r, s_next)."""
    state: np.ndarray
    action_idx: int
    reward: float
    prob: float  # probability of action under old policy


class LinearPPO:
    """Linear Proximal Policy Optimization (without neural networks).

    Parameters
    ----------
    state_dim:
        Dimension of the state vector.
    action_dim:
        Number of discrete actions.
    lr:
        Learning rate (default 0.01).
    eps:
        PPO clipping epsilon (default 0.2).
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        lr: float = 0.01,
        eps: float = 0.2,
    ) -> None:
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = lr
        self.eps = eps

        # Weights: (action_dim, state_dim)
        self.W = np.random.normal(0, 0.1, (action_dim, state_dim))
        self.b = np.zeros(action_dim)

    def select_action(self, state: np.ndarray) -> Tuple[int, float]:
        """Select action using softmax policy.  O(state_dim * action_dim).

        Returns
        -------
        Tuple[int, float]
            (action_idx, probability)
        """
        logits = self.W @ state + self.b
        # Softmax
        exp_logits = np.exp(logits - np.max(logits))  # Numerical stability
        probs = exp_logits / np.sum(exp_logits)
        
        action_idx = np.random.choice(self.action_dim, p=probs)
        return int(action_idx), float(probs[action_idx])

    def update(self, trajectory: List[Transition]) -> float:
        """Perform PPO update step.  O(T * state_dim * action_dim). (T-411)."""
        if not trajectory:
            return 0.0

        # Simple advantage: reward - mean_reward (no value function for MVP)
        rewards = np.array([t.reward for t in trajectory])
        advantages = rewards - np.mean(rewards)
        
        total_loss = 0.0
        
        # Gradient descent
        for t, adv in zip(trajectory, advantages):
            # Compute current prob
            logits = self.W @ t.state + self.b
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / np.sum(exp_logits)
            curr_prob = probs[t.action_idx]
            
            # PPO ratio
            ratio = curr_prob / (t.prob + 1e-8)
            
            # Clipped objective (T-413)
            surr1 = ratio * adv
            surr2 = np.clip(ratio, 1.0 - self.eps, 1.0 + self.eps) * adv
            loss = -min(surr1, surr2) # we want to maximize
            total_loss += loss
            
            # Simple manual gradient step for softmax policy
            # d_logits = probs - target (if target is one-hot of action)
            # but for PPO it's more complex. For MVP, we use a simpler heuristic:
            # move weights of the chosen action towards state if advantage is positive.
            grad = (1.0 - curr_prob) * adv if adv > 0 else -curr_prob * adv
            self.W[t.action_idx] += self.lr * grad * t.state
            self.b[t.action_idx] += self.lr * grad

        return float(total_loss / len(trajectory))

    def save_policy(self, path: str | Path) -> None:
        """Save weights to disk (T-414)."""
        with open(path, "wb") as f:
            pickle.dump({"W": self.W, "b": self.b}, f)

    def load_policy(self, path: str | Path) -> None:
        """Load weights from disk (T-414)."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.W = data["W"]
            self.b = data["b"]
