"""Phase 3 — KeywordExpander: BFS-based keyword expansion via Google Suggest.

Roadmap tasks: T-199 through T-212 (EPIC 3.4 SEO)

Algorithm
---------
BFS Expansion (T-201, T-202):
    1. Start with seed keywords from ContentPlan.
    2. Query Google Autocomplete (unauthenticated) for suggestions.
    3. Add unique suggestions to a queue and recurse up to depth 2.
    4. Complexity: O(V + E) where V = unique keywords, E = total suggestions.

Relevance Scoring (T-203):
    - Similarity based on keyword overlap and length.
    - O(n_keywords).

Deduplication (T-204):
    - Case-insensitive normalized key comparison.
    - O(n_keywords).
"""

from __future__ import annotations

import logging
import random
import time
from collections import deque
from typing import Dict, List, Set

import httpx

from modules.adapters.retry import retry, RetryableError

logger = logging.getLogger(__name__)

# Google Suggest API endpoint (no auth required)
_SUGGEST_URL = "https://suggestqueries.google.com/complete/search"
_DEFAULT_DEPTH = 1
_MAX_KEYWORDS = 30


class KeywordExpander:
    """Expands seed keywords using Google Autocomplete BFS.

    Parameters
    ----------
    client:
        Optional HTTPX client for making requests.
    """

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=10.0)

    def expand(self, seeds: List[str], depth: int = _DEFAULT_DEPTH) -> List[str]:
        """Expand seed keywords using a BFS traversal of Google Suggest.

        Algorithm: BFS O(V + E) (T-201).

        Parameters
        ----------
        seeds:
            Initial list of keywords to expand.
        depth:
            How many levels of suggestions to follow (default 1).

        Returns
        -------
        List[str]
            Expanded, deduplicated, and ranked list of keywords.
        """
        if not seeds:
            return []

        visited: Set[str] = set(s.lower().strip() for s in seeds)
        queue: deque[tuple[str, int]] = deque([(s, 0) for s in seeds])
        expanded: List[str] = list(seeds)

        while queue:
            keyword, current_depth = queue.popleft()
            if current_depth >= depth:
                continue

            try:
                suggestions = self._fetch_suggestions(keyword)
                for s in suggestions:
                    norm_s = s.lower().strip()
                    if norm_s not in visited and len(expanded) < _MAX_KEYWORDS:
                        visited.add(norm_s)
                        queue.append((s, current_depth + 1))
                        expanded.append(s)
            except Exception as exc:
                logger.warning("KeywordExpander: failed to expand '%s': %s", keyword, exc)

        # Sort by relevance (simple length/overlap proxy)
        # O(n log n)
        return self._rank_keywords(expanded, seeds)

    @retry(max_retries=3, base_delay=1.0)
    def _fetch_suggestions(self, keyword: str) -> List[str]:
        """Fetch autocomplete suggestions from Google.  O(1) request.

        Raises
        ------
        RetryableError
            On network timeout or 429/5xx.
        """
        params = {
            "client": "youtube",
            "q": keyword,
            "hl": "en",
        }
        try:
            response = self._client.get(_SUGGEST_URL, params=params)
            if response.status_code == 429:
                raise RetryableError("Rate limit exceeded")
            if response.status_code >= 500:
                raise RetryableError(f"Server error: {response.status_code}")
            
            response.raise_for_status()
            
            # Google returns: ["keyword", ["suggestion1", "suggestion2", ...], ...]
            data = response.json()
            if isinstance(data, list) and len(data) > 1:
                return [str(s) for s in data[1]]
            return []
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise RetryableError(f"HTTP error: {exc}")

    def _rank_keywords(self, keywords: List[str], seeds: List[str]) -> List[str]:
        """Rank expanded keywords by relevance to seeds.  O(n log n)."""
        seed_words = set()
        for s in seeds:
            seed_words.update(s.lower().split())

        def score(kw: str) -> float:
            kw_lower = kw.lower()
            overlap = sum(1 for w in kw_lower.split() if w in seed_words)
            # Preference for medium length (2-4 words)
            len_penalty = abs(3 - len(kw_lower.split())) * 0.1
            return overlap - len_penalty

        return sorted(keywords, key=score, reverse=True)
