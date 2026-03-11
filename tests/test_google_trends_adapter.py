"""Tests for GoogleTrendsTrendSource — T-031 to T-036."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from modules.adapters.google_trends import GoogleTrendsTrendSource
from ytaimbot_ml.schemas import TrendSignal


def _make_entry(keyword: str) -> str:
    return keyword


@pytest.fixture
def mock_trendspy_data():
    """20 fake trending keywords."""
    return [f"trend keyword {i}" for i in range(20)]


def test_fetch_returns_trend_signals(mock_trendspy_data):
    """fetch() must return list[TrendSignal]."""
    with patch.dict("sys.modules", {"trendspy": _make_trendspy_mock(mock_trendspy_data)}):
        src = GoogleTrendsTrendSource(geo="US")
        signals = src.fetch()

    assert isinstance(signals, list)
    assert len(signals) >= 1
    assert all(isinstance(s, TrendSignal) for s in signals)


def test_fetch_raw_score_in_range(mock_trendspy_data):
    """All raw_scores must be in [0.0, 1.0]."""
    with patch.dict("sys.modules", {"trendspy": _make_trendspy_mock(mock_trendspy_data)}):
        src = GoogleTrendsTrendSource(geo="US")
        signals = src.fetch()

    assert all(0.0 <= s.raw_score <= 1.0 for s in signals), (
        "raw_score out of [0.0, 1.0] range"
    )


def test_fetch_respects_max_results(mock_trendspy_data):
    """fetch() must not exceed max_results."""
    with patch.dict("sys.modules", {"trendspy": _make_trendspy_mock(mock_trendspy_data)}):
        src = GoogleTrendsTrendSource(geo="US", max_results=5)
        signals = src.fetch()

    assert len(signals) <= 5


def test_fetch_source_field(mock_trendspy_data):
    """TrendSignal.source must be 'google_trends'."""
    with patch.dict("sys.modules", {"trendspy": _make_trendspy_mock(mock_trendspy_data)}):
        src = GoogleTrendsTrendSource(geo="US")
        signals = src.fetch()

    assert all(s.source == "google_trends" for s in signals)


def test_fetch_geo_parameter():
    """geo parameter must be passed through to trendspy."""
    calls = []

    class MockTrends:
        def trending_now(self, geo="US"):
            calls.append(geo)
            return [f"kw{i}" for i in range(5)]

    mock_module = MagicMock()
    mock_module.Trends.return_value = MockTrends()

    with patch.dict("sys.modules", {"trendspy": mock_module}):
        src = GoogleTrendsTrendSource(geo="UA")
        src.fetch()

    assert calls == ["UA"]


def test_network_error_falls_back_to_synthetic():
    """Any network exception → fallback to SyntheticTrendSource."""
    mock_module = MagicMock()
    mock_module.Trends.return_value.trending_now.side_effect = ConnectionError("timeout")

    with patch.dict("sys.modules", {"trendspy": mock_module}):
        src = GoogleTrendsTrendSource(geo="US")
        # Patch retry to not sleep
        with patch("time.sleep"):
            signals = src.fetch()

    assert isinstance(signals, list)
    assert len(signals) >= 1
    assert all(isinstance(s, TrendSignal) for s in signals)


def test_determinism_same_data():
    """Same input entries → same output TrendSignal list."""
    data = [f"kw{i}" for i in range(10)]

    with patch.dict("sys.modules", {"trendspy": _make_trendspy_mock(data)}):
        src1 = GoogleTrendsTrendSource(geo="US")
        signals1 = src1.fetch()

    with patch.dict("sys.modules", {"trendspy": _make_trendspy_mock(data)}):
        src2 = GoogleTrendsTrendSource(geo="US")
        signals2 = src2.fetch()

    assert [s.keyword for s in signals1] == [s.keyword for s in signals2]
    assert [s.raw_score for s in signals1] == [s.raw_score for s in signals2]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_trendspy_mock(data: list[str]) -> MagicMock:
    mock_module = MagicMock()
    mock_module.Trends.return_value.trending_now.return_value = data
    return mock_module
