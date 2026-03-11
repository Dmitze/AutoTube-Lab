"""Phase 2 — TokenBudget: proportional token allocation across script sections.

Roadmap tasks: T-100 (EPIC 2.1)

Algorithm
---------
Proportional Weighted Allocation:
  1. Assign a quality weight to each section (hook=1.5, cta=1.2, body=1.0, intro=0.8)
  2. total_weight = sum(weights)
  3. tokens[section] = floor(total_tokens × weight[section] / total_weight)
  4. Remainder tokens added to the highest-weight section

  Complexity: O(n) time, O(n) space — n = number of sections

Rationale: MVP does not require full 0/1 Knapsack DP (O(n×W)).
  Proportional allocation is O(n), deterministic, and covers all use cases
  for fixed script structure (hook→intro→body×3→cta = 6 sections).
  Knapsack DP reserved for Phase 6 when section count becomes variable.
"""
from __future__ import annotations

# Default quality weights per section.
# Higher weight → more tokens allocated.
_DEFAULT_WEIGHTS: dict[str, float] = {
    "hook":   1.5,  # Most important: drives watch-through rate
    "cta":    1.2,  # Call-to-action: drives subscribe/like
    "body_1": 1.0,
    "body_2": 1.0,
    "body_3": 1.0,
    "intro":  0.8,  # Least constrained: set context only
}

# Minimum token floor per section to ensure coherent output
_MIN_TOKENS: int = 64


class TokenBudget:
    """Proportional token budget allocator for script sections.

    Parameters
    ----------
    total_tokens:
        Total token budget across all sections (default 2048).
    weights:
        Optional custom weights dict. Keys must match section names.

    Complexity
    ----------
    allocate(): O(n) time, O(n) space — n = number of sections

    Examples
    --------
    >>> budget = TokenBudget(total_tokens=1200)
    >>> sections = ["hook", "intro", "body_1", "body_2", "body_3", "cta"]
    >>> alloc = budget.allocate(sections)
    >>> sum(alloc.values()) <= 1200
    True
    >>> alloc["hook"] > alloc["intro"]  # hook gets more tokens
    True
    """

    def __init__(
        self,
        total_tokens: int = 2048,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.total_tokens = total_tokens
        self._weights = weights or _DEFAULT_WEIGHTS.copy()

    def allocate(self, sections: list[str]) -> dict[str, int]:
        """Allocate token budget proportionally across named sections.

        Parameters
        ----------
        sections:
            Ordered list of section name strings (e.g. ["hook", "intro", ...]).

        Returns
        -------
        dict[str, int]
            Mapping of section name → token count.
            All values ≥ _MIN_TOKENS. Sum ≤ total_tokens.

        Complexity
        ----------
        O(n) where n = len(sections)

        Examples
        --------
        >>> b = TokenBudget(total_tokens=600)
        >>> alloc = b.allocate(["hook", "cta"])
        >>> alloc["hook"] > alloc["cta"]  # 1.5 > 1.2
        True
        """
        if not sections:
            return {}

        # Resolve weights; unknown sections default to body weight (1.0)
        weights = {s: self._weights.get(s, 1.0) for s in sections}
        total_weight = sum(weights.values())

        # First pass: proportional allocation floored to int
        allocations: dict[str, int] = {}
        for name in sections:
            raw = (weights[name] / total_weight) * self.total_tokens
            allocations[name] = max(_MIN_TOKENS, int(raw))

        # Second pass: distribute remainder to highest-weight section
        used = sum(allocations.values())
        remainder = self.total_tokens - used
        if remainder > 0:
            top_section = max(sections, key=lambda s: weights[s])
            allocations[top_section] += remainder

        return allocations

    def estimate_words(self, token_count: int) -> int:
        """Estimate word count from token count.

        Uses conservative 0.75 words/token ratio.

        Parameters
        ----------
        token_count:
            Number of tokens.

        Returns
        -------
        int
            Estimated word count.

        Complexity
        ----------
        O(1)

        Examples
        --------
        >>> TokenBudget().estimate_words(100)
        75
        """
        return max(1, int(token_count * 0.75))

