"""LRU Cache with TTL for trend adapter responses.

Algorithm
---------
LRU Cache (T-061, T-062, T-063):
    Backed by ``collections.OrderedDict`` for O(1) get/put.

    get(key):
        1. Miss or expired → return None            O(1)
        2. Hit → move_to_end (mark recent) → return  O(1)

    put(key, value):
        1. Insert at end with current timestamp      O(1)
        2. Evict LRU (front) when len > capacity     O(1)

Usage
-----
    from modules.adapters.cache import TrendCache

    cache: TrendCache[list] = TrendCache(capacity=64, ttl_seconds=900)
    cache.put("us_trends", signals)
    hits = cache.get("us_trends")   # None after 15 minutes
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Generic, TypeVar

V = TypeVar("V")

_DEFAULT_CAPACITY = 128
_DEFAULT_TTL = 900  # 15 minutes — trends don't change faster


class TrendCache(Generic[V]):
    """Thread-unsafe LRU cache with per-entry TTL.

    Parameters
    ----------
    capacity:
        Maximum number of entries to store.  Oldest entry is evicted
        when the limit is exceeded.
    ttl_seconds:
        Time-to-live in seconds.  Expired entries are treated as missing.

    Complexity
    ----------
    get / put: O(1) amortized (OrderedDict move_to_end is O(1)).

    Examples
    --------
    >>> c: TrendCache[int] = TrendCache(capacity=2, ttl_seconds=60)
    >>> c.put("a", 1)
    >>> c.get("a")
    1
    >>> c.get("missing")  # None for cache miss
    """

    def __init__(
        self,
        capacity: int = _DEFAULT_CAPACITY,
        ttl_seconds: float = _DEFAULT_TTL,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._ttl = ttl_seconds
        # OrderedDict: key → (value, inserted_at)
        self._store: OrderedDict[str, tuple[V, float]] = OrderedDict()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> V | None:
        """Return cached value or ``None`` on miss / expiry.

        Complexity: O(1)
        """
        if key not in self._store:
            return None

        value, ts = self._store[key]
        if time.monotonic() - ts > self._ttl:
            del self._store[key]
            return None

        self._store.move_to_end(key)  # mark as recently used
        return value

    def put(self, key: str, value: V) -> None:
        """Insert or update *key* with *value*.

        Evicts the least-recently-used entry when at capacity.

        Complexity: O(1)
        """
        if key in self._store:
            del self._store[key]

        self._store[key] = (value, time.monotonic())
        self._store.move_to_end(key)

        if len(self._store) > self._capacity:
            self._store.popitem(last=False)  # evict LRU (front)

    def invalidate(self, key: str) -> None:
        """Remove *key* from the cache (no-op if absent)."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Evict all entries."""
        self._store.clear()

    @property
    def size(self) -> int:
        """Number of non-expired entries currently stored."""
        return len(self._store)
