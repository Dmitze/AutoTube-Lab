"""Tests for GoogleTrendsAdapter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
import trendspy
import pandas as pd # Import pandas for DataFrame mocking

from modules.adapters.base import TrendSourceAdapter
from modules.adapters.errors import RetryableError
from modules.adapters.synthetic import SyntheticTrendSource
from ytaimbot_ml.schemas import TrendSignal

# Mock Item for trendspy.Trends().trending_now()
class MockTrendKeyword:
    def __init__(self, keyword, volume, started_timestamp):
        self.keyword = keyword
        self.volume = volume
        self.started_timestamp = started_timestamp

MOCK_TRENDSPY_ITEMS = [
    MockTrendKeyword("Quantum Computing", 5000000, [1780308000]), # 2026-06-01T10:00:00Z
    MockTrendKeyword("AI Ethics", 0, [1780311600]), # 2026-06-01T11:00:00Z
]

class TestGoogleTrendsAdapter:
    """Tests for the GoogleTrendsAdapter."""

    @patch("trendspy.Trends")
    def test_fetch_returns_trend_signals(self, mock_trends_class: MagicMock) -> None:
        """
        fetch() should call trendspy.Trends().trending_now and return a list of TrendSignal objects.
        """
        from modules.adapters.google_trends import GoogleTrendsAdapter

        mock_client = MagicMock()
        mock_trends_class.return_value = mock_client
        mock_client.trending_now.return_value = MOCK_TRENDSPY_ITEMS

        adapter = GoogleTrendsAdapter(geo="US")
        
        signals = adapter.fetch()

        mock_client.trending_now.assert_called_once_with(geo="US")

        assert isinstance(signals, list)
        assert len(signals) == 2
        assert all(isinstance(s, TrendSignal) for s in signals)

        signal1 = signals[0]
        assert signal1.trend_id == "quantum-computing"
        assert signal1.keyword == "Quantum Computing"
        assert signal1.raw_score == 0.5 # 5000000 / 10000000
        assert signal1.source == "Google Trends"

        signal2 = signals[1]
        assert signal2.trend_id == "ai-ethics"
        assert signal2.keyword == "AI Ethics"
        assert signal2.raw_score == 0.0

    @patch("trendspy.Trends")
    @patch("time.sleep")
    @patch("modules.adapters.retry.random.random", return_value=0.0)
    def test_fetch_retries_on_failure(self, mock_random: MagicMock, mock_sleep: MagicMock, mock_trends_class: MagicMock) -> None:
        """
        fetch() should retry on transient failures with exponential backoff and jitter.
        """
        from modules.adapters.google_trends import GoogleTrendsAdapter

        mock_client = MagicMock()
        mock_trends_class.return_value = mock_client
        mock_client.trending_now.side_effect = [
            RetryableError("Transient error"),
            RetryableError("Another transient error"),
            MOCK_TRENDSPY_ITEMS, # Success on third attempt
        ]

        adapter = GoogleTrendsAdapter(geo="US")
        
        signals = adapter.fetch()

        assert mock_client.trending_now.call_count == 3
        mock_client.trending_now.assert_called_with(geo="US")

        mock_sleep.assert_any_call(2.0)
        mock_sleep.assert_any_call(4.0)
        assert mock_sleep.call_count == 2

        assert len(signals) == 2
        assert signals[0].keyword == "Quantum Computing"
    
    @patch("trendspy.Trends")
    def test_fetch_falls_back_to_synthetic(self, mock_trends_class: MagicMock) -> None:
        """
        fetch() should fallback to SyntheticTrendSource if trendspy fails persistently.
        """
        from modules.adapters.google_trends import GoogleTrendsAdapter

        mock_client = MagicMock()
        mock_trends_class.return_value = mock_client
        mock_client.trending_now.side_effect = RetryableError("Persistent error")

        fallback_source = SyntheticTrendSource(seed=0)
        adapter = GoogleTrendsAdapter(geo="US", fallback_source=fallback_source)
        
        signals = adapter.fetch()

        assert mock_client.trending_now.call_count == 4
        mock_client.trending_now.assert_called_with(geo="US")

        assert len(signals) == 10
        assert all(isinstance(s, TrendSignal) for s in signals)
        assert signals[0].source == "synthetic"
        assert signals[0].keyword == "ai_automation"
