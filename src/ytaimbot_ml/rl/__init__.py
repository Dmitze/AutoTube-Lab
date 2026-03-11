"""Phase 6 — Reinforcement Learning package.

Modules
-------
ucb1_bandit    : UCB1 multi-armed bandit for content strategy selection
reward_shaper  : Reward normalization and shaping

Algorithm
---------
UCB1 action selection:
  a* = argmax_i [ x̄_i + √(2 ln N / n_i) ]
  - x̄_i = empirical mean reward for arm i
  - N    = total pulls, n_i = pulls of arm i
  - Regret bound: O(√(k N ln N))

Reward shaping:
  r_shaped = clip((r - μ) / σ, -3, 3) → normalized [-3, 3]

Status: 🔲 Pending — T-500 (Phase 6)
"""
