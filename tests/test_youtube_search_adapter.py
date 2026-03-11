"""Tests for YouTubeSearchTrendSource and QuotaTracker — T-045 to T-050."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from modules.adapters.youtube_search import QuotaTracker, YouTubeSearchTrendSource
from ytaimbot_ml.schemas import TrendSignal


# ---------------------------------------------------------------------------
# QuotaTracker tests (T-049, T-050)
# ---------------------------------------------------------------------------

def test_quota_tracker_allows_initial_request():
    qt = QuotaTracker(daily_budget=10_000)
    assert qt.can_proceed(100) is True


def test_quota_tracker_counts_correctly():
    qt = QuotaTracker(daily_budget=500)
    qt.record(100)
    qt.record(200)
    assert qt.remaining == 200


def test_quota_tracker_blocks_when_exceeded():
    qt = QuotaTracker(daily_budget=200)
    qt.record(200)
    assert qt.can_proceed(1) is False


def test_quota_tracker_resets_after_window(monkeypatch):
    """After the 24 h window, quota should reset."""
    import time as _time

    qt = QuotaTracker(daily_budget=200)
    qt.record(200)
    assert qt.can_proceed(1) is False

    # Advance clock by 24 h + 1 s
    original = _time.monotonic
    monkeypatch.setattr(_time, "monotonic", lambda: original() + 86_401)
    assert qt.can_proceed(100) is True


# ---------------------------------------------------------------------------
# YouTubeSearchTrendSource tests (T-045 – T-048)
# ---------------------------------------------------------------------------

def test_fetch_without_api_key_returns_synthetic():
    """No API key → graceful degradation to synthetic source."""
    src = YouTubeSearchTrendSource(api_key="")
    signals = src.fetch()

    assert isinstance(signals, list)
    assert len(signals) >= 1
    assert all(isinstance(s, TrendSignal) for s in signals)


def test_fetch_returns_trend_signals():
    """With mocked API, fetch() returns list[TrendSignal]."""
    src = YouTubeSearchTrendSource(api_key="fake_key")
    src._quota = _make_unlimited_quota()

    with patch.object(src, "_call_api", return_value=_fake_signals(5)):
        signals = src.fetch()

    assert len(signals) == 5
    assert all(isinstance(s, TrendSignal) for s in signals)


def test_fetch_quota_exceeded_returns_synthetic():
    """When quota is exhausted, fetch must fall back to synthetic."""
    src = YouTubeSearchTrendSource(api_key="fake_key")
    src._quota = _make_exhausted_quota()

    signals = src.fetch()

    assert isinstance(signals, list)
    assert len(signals) >= 1


def test_missing_api_key_env_var(monkeypatch):
    """YOUTUBE_API_KEY not set → ValueError-like fallback (no crash)."""
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    src = YouTubeSearchTrendSource()  # no api_key arg, no env var
    signals = src.fetch()
    assert isinstance(signals, list)


def test_parse_response_score_in_range():
    """Parsed scores must be in [0.0, 1.0]."""
    src = YouTubeSearchTrendSource(api_key="x")
    response = {
        "items": [
            {"id": {"videoId": f"v{i}"}, "snippet": {"title": f"Video {i}"}}
            for i in range(10)
        ]
    }
    signals = src._parse_response(response)
    assert all(0.0 <= s.raw_score <= 1.0 for s in signals)


def test_parse_response_source_field():
    src = YouTubeSearchTrendSource(api_key="x")
    response = {
        "items": [{"id": {"videoId": "abc"}, "snippet": {"title": "Test"}}]
    }
    signals = src._parse_response(response)
    assert signals[0].source == "youtube_search"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_signals(n: int) -> list[TrendSignal]:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    return [
        TrendSignal(
            trend_id=f"yt_v{i}",
            keyword=f"keyword {i}",
            raw_score=1.0 - i / n,
            source="youtube_search",
            timestamp=now,
        )
        for i in range(n)
    ]


def _make_unlimited_quota() -> QuotaTracker:
    qt = QuotaTracker(daily_budget=10_000)
    return qt


def _make_exhausted_quota() -> QuotaTracker:
    qt = QuotaTracker(daily_budget=100)
    qt.record(100)
    return qt
