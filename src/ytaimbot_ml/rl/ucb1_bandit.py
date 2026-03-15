"""Phase 6 — UCB1Bandit: Upper Confidence Bound 1 multi-armed bandit.

Roadmap tasks: T-500 through T-520 (EPIC 6.1 Bandit Algorithm)
Depends on:   EMATracker (Phase 5 rewards)

Algorithm
---------
UCB1 (Auer, Cesa-Bianchi, Fischer 2002):

  Action selection:
    a* = argmax_i [ x̄_i + √(2 ln N / n_i) ]
    - x̄_i : mean reward of arm i
    - N    : total pulls across all arms
    - n_i  : number of times arm i was selected

    Tie-breaking: arm with fewest pulls (exploration priority).
    If still tied, the provided RNG is used for fairness.

  Update:
    x̄_i ← (x̄_i × n_i + r) / (n_i + 1)    (incremental mean)

  Complexity:
    select()  → O(k)  where k = number of arms
    update()  → O(1)
    Regret:     O(√(k N ln N))  (sub-linear, proven optimal)
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass

import numpy as np

from ytaimbot_ml.utils.random import make_rng

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data container
# ---------------------------------------------------------------------------


@dataclass
class ArmStats:
    """Per-arm statistics for the UCB1 bandit.

    Attributes
    ----------
    arm_id:
        Unique identifier for this arm (e.g. niche name).
    n_pulls:
        Number of times this arm has been selected.
    total_reward:
        Cumulative reward received from this arm.
    last_reward:
        Most recent reward value.
    """

    arm_id: str
    n_pulls: int = 0
    total_reward: float = 0.0
    last_reward: float = 0.0

    @property
    def avg_reward(self) -> float:
        """Mean reward across all pulls.

        Returns ``0.0`` when the arm has never been pulled.

        Complexity: O(1).
        """
        return self.total_reward / self.n_pulls if self.n_pulls > 0 else 0.0


# ---------------------------------------------------------------------------
# Bandit
# ---------------------------------------------------------------------------


class UCB1Bandit:
    """UCB1 multi-armed bandit for YouTube niche selection.

    Select which niche to produce a video for next, then receive reward
    feedback based on actual video performance.

    Algorithm: UCB1 — Upper Confidence Bound
      select: O(k) where k = number of arms
      update: O(1)

    Parameters
    ----------
    arm_ids:
        List of niche/strategy identifiers (the "arms").
    rng:
        NumPy random Generator for tie-breaking.  Pass ``None`` to use a
        default seeded generator (seed 42).

    Examples
    --------
    >>> bandit = UCB1Bandit(arm_ids=["ghibli", "finance", "ai_tech"])
    >>> arm = bandit.select()
    >>> arm in ["ghibli", "finance", "ai_tech"]
    True
    >>> bandit.update(arm, reward=0.8)
    >>> bandit.stats[arm].n_pulls
    1
    """

    # Phase P13 (T-949): default niche arms for monetization strategy routing.
    DEFAULT_NICHE_ARMS: tuple[str, str, str] = (
        "ghibli_asmr",
        "hype_characters",
        "ai_stories",
    )

    def __init__(
        self,
        arm_ids: list[str],
        rng: np.random.Generator | None = None,
    ) -> None:
        """Initialise the bandit.

        Parameters
        ----------
        arm_ids:
            Non-empty list of unique arm identifiers.
        rng:
            RNG for tie-breaking.  Defaults to ``make_rng(42)``.

        Raises
        ------
        ValueError
            If ``arm_ids`` is empty or contains duplicates.

        Complexity: O(k).
        """
        if not arm_ids:
            raise ValueError("arm_ids must be non-empty.")
        if len(arm_ids) != len(set(arm_ids)):
            raise ValueError("arm_ids must be unique.")
        self._rng: np.random.Generator = rng if rng is not None else make_rng(42)
        self._arms: dict[str, ArmStats] = {
            arm_id: ArmStats(arm_id=arm_id) for arm_id in arm_ids
        }
        self._total_pulls: int = 0
        logger.info("UCB1Bandit initialised with %d arms: %s", len(arm_ids), arm_ids)

    @classmethod
    def for_niches(
        cls,
        rng: np.random.Generator | None = None,
        arm_ids: list[str] | None = None,
    ) -> "UCB1Bandit":
        """Build a bandit preconfigured for default content niches.

        Parameters
        ----------
        rng:
            Optional RNG for deterministic tie-breaking.
        arm_ids:
            Optional override list. When omitted, uses
            ``DEFAULT_NICHE_ARMS`` (Ghibli, Hype, AI Stories).

        Returns
        -------
        UCB1Bandit
            Initialised bandit with niche arms.

        Complexity
        ----------
        O(k) where k = number of arms.

        Examples
        --------
        >>> b = UCB1Bandit.for_niches()
        >>> set(UCB1Bandit.DEFAULT_NICHE_ARMS).issubset(set(b.stats))
        True
        """
        selected_arms = list(arm_ids) if arm_ids is not None else list(cls.DEFAULT_NICHE_ARMS)
        return cls(arm_ids=selected_arms, rng=rng)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def select(self) -> str:
        """Choose which arm to pull next using the UCB1 policy.

        First round: cycles through all arms exactly once (pure exploration)
        in insertion order to ensure every arm gets at least one observation.

        Subsequent rounds: selects the arm with the highest UCB1 score:
            UCB1(i) = avg_reward(i) + sqrt(2 * ln(total_pulls) / n_pulls(i))

        Ties are broken by fewest pulls first; remaining ties are broken
        uniformly at random using the instance RNG.

        Returns
        -------
        str
            The arm_id of the selected arm.

        Complexity: O(k).

        Examples
        --------
        >>> b = UCB1Bandit(arm_ids=["a", "b", "c"])
        >>> first = b.select()
        >>> first in ["a", "b", "c"]
        True
        """
        # Exploration: pull each arm at least once before using UCB1.
        unplayed = [arm for arm in self._arms.values() if arm.n_pulls == 0]
        if unplayed:
            chosen = unplayed[0]
            logger.debug("UCB1 exploration: selecting unplayed arm '%s'.", chosen.arm_id)
            return chosen.arm_id

        log_total = math.log(self._total_pulls)
        scores: list[tuple[float, int, str]] = []
        for arm in self._arms.values():
            ucb = arm.avg_reward + math.sqrt(2.0 * log_total / arm.n_pulls)
            scores.append((ucb, arm.n_pulls, arm.arm_id))

        best_score = max(s[0] for s in scores)
        candidates = [s for s in scores if s[0] == best_score]

        # Tie-break 1: fewest pulls
        min_pulls = min(c[1] for c in candidates)
        candidates = [c for c in candidates if c[1] == min_pulls]

        # Tie-break 2: random
        idx = int(self._rng.integers(len(candidates)))
        arm_id = candidates[idx][2]
        logger.debug(
            "UCB1 select: arm='%s' score=%.6f total_pulls=%d",
            arm_id,
            best_score,
            self._total_pulls,
        )
        return arm_id

    def update(self, arm_id: str, reward: float) -> None:
        """Record a reward for a previously selected arm.

        The reward is clamped to ``[0.0, 1.0]`` before being applied.

        Parameters
        ----------
        arm_id:
            Arm that was pulled.
        reward:
            Observed reward.  Values outside ``[0, 1]`` are clamped silently.

        Raises
        ------
        KeyError
            If ``arm_id`` is not registered.

        Complexity: O(1).
        """
        if arm_id not in self._arms:
            raise KeyError(f"Unknown arm: {arm_id!r}")
        reward = float(np.clip(reward, 0.0, 1.0))
        arm = self._arms[arm_id]
        arm.n_pulls += 1
        arm.total_reward += reward
        arm.last_reward = reward
        self._total_pulls += 1
        logger.debug(
            "UCB1 update: arm='%s' reward=%.4f avg_reward=%.4f n_pulls=%d",
            arm_id,
            reward,
            arm.avg_reward,
            arm.n_pulls,
        )

    def best_arm(self) -> str:
        """Return the arm with the highest average reward.

        Ties are broken by the arm that appears first in insertion order.

        Returns
        -------
        str
            arm_id with highest ``avg_reward``.

        Complexity: O(k).

        Examples
        --------
        >>> b = UCB1Bandit(arm_ids=["a", "b"])
        >>> b.update("a", 1.0); b.update("b", 0.2)
        >>> b.best_arm()
        'a'
        """
        return max(self._arms.values(), key=lambda a: a.avg_reward).arm_id

    def reset(self) -> None:
        """Reset all arm statistics to zero.

        Does **not** change ``arm_ids`` or ``rng``.

        Complexity: O(k).

        Examples
        --------
        >>> b = UCB1Bandit(arm_ids=["a", "b"])
        >>> b.update("a", 0.5)
        >>> b.reset()
        >>> b.stats["a"].n_pulls
        0
        """
        for arm in self._arms.values():
            arm.n_pulls = 0
            arm.total_reward = 0.0
            arm.last_reward = 0.0
        self._total_pulls = 0
        logger.debug("UCB1Bandit reset: all arms cleared.")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def stats(self) -> dict[str, ArmStats]:
        """Read-only view of per-arm statistics.

        Returns
        -------
        dict[str, ArmStats]
            Mapping of arm_id → :class:`ArmStats`.

        Complexity: O(1).
        """
        return self._arms

    @property
    def total_pulls(self) -> int:
        """Total number of pulls across all arms.

        Complexity: O(1).
        """
        return self._total_pulls

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise bandit state to a plain dictionary.

        Returns
        -------
        dict
            Contains ``"total_pulls"`` and ``"arms"`` (list of arm dicts).

        Complexity: O(k).

        Examples
        --------
        >>> b = UCB1Bandit(arm_ids=["ghibli"])
        >>> b.update("ghibli", 0.9)
        >>> d = b.to_dict()
        >>> d["arms"][0]["arm_id"]
        'ghibli'
        """
        return {
            "total_pulls": self._total_pulls,
            "arms": [
                {
                    "arm_id": arm.arm_id,
                    "n_pulls": arm.n_pulls,
                    "total_reward": arm.total_reward,
                    "last_reward": arm.last_reward,
                }
                for arm in self._arms.values()
            ],
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
        rng: np.random.Generator | None = None,
    ) -> "UCB1Bandit":
        """Deserialise a bandit from a dictionary produced by :meth:`to_dict`.

        Parameters
        ----------
        data:
            Dictionary as returned by :meth:`to_dict`.
        rng:
            Optional RNG override; defaults to ``make_rng(42)``.

        Returns
        -------
        UCB1Bandit
            Fully restored instance.

        Complexity: O(k).

        Examples
        --------
        >>> b = UCB1Bandit(arm_ids=["a", "b"])
        >>> b.update("a", 0.6)
        >>> restored = UCB1Bandit.from_dict(b.to_dict())
        >>> restored.stats["a"].n_pulls
        1
        """
        arm_ids = [a["arm_id"] for a in data["arms"]]
        obj = cls(arm_ids=arm_ids, rng=rng)
        obj._total_pulls = int(data["total_pulls"])
        for arm_data in data["arms"]:
            arm = obj._arms[arm_data["arm_id"]]
            arm.n_pulls = int(arm_data["n_pulls"])
            arm.total_reward = float(arm_data["total_reward"])
            arm.last_reward = float(arm_data["last_reward"])
        return obj

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"UCB1Bandit(arms={list(self._arms)}, "
            f"total_pulls={self._total_pulls})"
        )
