"""Tests for TrendCache (LRU + TTL) — T-065 to T-068."""

from __future__ import annotations

import time

import pytest

from modules.adapters.cache import TrendCache


def test_cache_hit_returns_value():
    cache: TrendCache[int] = TrendCache(capacity=10, ttl_seconds=60)
    cache.put("key1", 99)
    assert cache.get("key1") == 99


def test_cache_miss_returns_none():
    cache: TrendCache[str] = TrendCache(capacity=10, ttl_seconds=60)
    assert cache.get("nonexistent") is None


def test_ttl_expired_returns_none(monkeypatch):
    """After TTL expires the cache entry should be evicted."""
    cache: TrendCache[int] = TrendCache(capacity=10, ttl_seconds=1.0)
    cache.put("k", 42)

    # Advance monotonic clock past TTL
    original = time.monotonic
    monkeypatch.setattr(time, "monotonic", lambda: original() + 2.0)

    assert cache.get("k") is None


def test_lru_eviction_when_at_capacity():
    """When capacity is exceeded, the least-recently-used entry is evicted."""
    cache: TrendCache[int] = TrendCache(capacity=2, ttl_seconds=60)
    cache.put("a", 1)
    cache.put("b", 2)

    # Access "a" to make it recently used
    assert cache.get("a") == 1

    # Insert "c" → "b" is LRU and must be evicted
    cache.put("c", 3)

    assert cache.get("a") == 1   # recently used → kept
    assert cache.get("c") == 3   # just inserted → kept
    assert cache.get("b") is None  # LRU → evicted


def test_put_updates_existing_key():
    cache: TrendCache[str] = TrendCache(capacity=5, ttl_seconds=60)
    cache.put("x", "old")
    cache.put("x", "new")
    assert cache.get("x") == "new"
    assert cache.size == 1


def test_size_reports_correct_count():
    cache: TrendCache[int] = TrendCache(capacity=5, ttl_seconds=60)
    assert cache.size == 0
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.size == 2


def test_invalidate_removes_key():
    cache: TrendCache[int] = TrendCache(capacity=5, ttl_seconds=60)
    cache.put("a", 1)
    cache.invalidate("a")
    assert cache.get("a") is None


def test_clear_empties_cache():
    cache: TrendCache[int] = TrendCache(capacity=5, ttl_seconds=60)
    for i in range(3):
        cache.put(str(i), i)
    cache.clear()
    assert cache.size == 0


def test_invalid_capacity_raises():
    with pytest.raises(ValueError, match="capacity"):
        TrendCache(capacity=0)
