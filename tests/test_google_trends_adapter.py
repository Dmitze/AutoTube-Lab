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

# Mock DataFrame data for trendspy.get_trends
MOCK_TRENDSPY_DATAFRAME = pd.DataFrame(
    {
        "search_term": ["Quantum Computing", "AI Ethics"],
        "date": [
            datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc), # Ensure timezone-aware
            datetime(2026, 6, 1, 11, 0, 0, tzinfo=timezone.utc), # Ensure timezone-aware
        ],
        # Add other columns that might be returned by get_trends if needed for parsing
        # For simplicity, we only include 'search_term' and 'date' as they are used
        # to construct TrendSignal.
    }
)


class TestGoogleTrendsAdapter:
    """Tests for the GoogleTrendsAdapter."""

    @patch("trendspy.get_trends") # Corrected mock target
    def test_fetch_returns_trend_signals(self, mock_get_trends: MagicMock) -> None:
        """
        fetch() should call trendspy.get_trends and return a list of TrendSignal objects.
        """
        from modules.adapters.google_trends import GoogleTrendsAdapter

        mock_get_trends.return_value = MOCK_TRENDSPY_DATAFRAME
        adapter = GoogleTrendsAdapter(geo="US")
        
        signals = adapter.fetch()

        # Verify trendspy.get_trends was called with correct arguments
        # The query is defined in the adapter's __init__ using os.environ.get
        expected_query = os.environ.get("GOOGLE_TRENDS_QUERY", "trending searches")
        mock_get_trends.assert_called_once_with(query=expected_query, geo="US")

        # Verify the returned data is a list of TrendSignal
        assert isinstance(signals, list)
        assert len(signals) == 2
        assert all(isinstance(s, TrendSignal) for s in signals)

        # Verify content of the first TrendSignal
        signal1 = signals[0]
        assert signal1.trend_id == "quantum-computing"
        assert signal1.keyword == "Quantum Computing"
        assert signal1.raw_score == 0 # As per new implementation
        assert signal1.source == "Google Trends"
        assert signal1.timestamp == "2026-06-01T10:00:00Z" # ISO-8601 UTC

        # Verify content of the second TrendSignal
        signal2 = signals[1]
        assert signal2.trend_id == "ai-ethics"
        assert signal2.keyword == "AI Ethics"
        assert signal2.raw_score == 0
        assert signal2.source == "Google Trends"
        assert signal2.timestamp == "2026-06-01T11:00:00Z"
    
    @patch("trendspy.get_trends") # Corrected mock target
    @patch("time.sleep")
    @patch("modules.adapters.retry.random.random", return_value=0.0)
    def test_fetch_retries_on_failure(self, mock_random: MagicMock, mock_sleep: MagicMock, mock_get_trends: MagicMock) -> None:
        """
        fetch() should retry on transient failures with exponential backoff and jitter.
        """
        from modules.adapters.google_trends import GoogleTrendsAdapter

        # Simulate transient failures then success
        mock_get_trends.side_effect = [
            RetryableError("Transient error"),
            RetryableError("Another transient error"),
            MOCK_TRENDSPY_DATAFRAME, # Success on third attempt
        ]

        adapter = GoogleTrendsAdapter(geo="US")
        
        signals = adapter.fetch()

        # Verify trendspy.get_trends was called 3 times
        assert mock_get_trends.call_count == 3
        expected_query = os.environ.get("GOOGLE_TRENDS_QUERY", "trending searches")
        mock_get_trends.assert_called_with(query=expected_query, geo="US")

        # Expected sleep calls for max_retries=3, base_delay=2.0, jitter=True (but random is mocked to 0.0)
        # 1st retry delay: 2.0 * (1 + 0.0) = 2.0s
        # 2nd retry delay: 4.0 * (1 + 0.0) = 4.0s
        mock_sleep.assert_any_call(2.0)
        mock_sleep.assert_any_call(4.0)
        assert mock_sleep.call_count == 2

        # Verify success after retries
        assert len(signals) == 2
        assert signals[0].keyword == "Quantum Computing" # Keyword from mock DataFrame
    
    @patch("trendspy.get_trends") # Corrected mock target
    def test_fetch_falls_back_to_synthetic(self, mock_get_trends: MagicMock) -> None:
        """
        fetch() should fallback to SyntheticTrendSource if trendspy fails persistently.
        """
        from modules.adapters.google_trends import GoogleTrendsAdapter

        # Simulate persistent failures (more than max_retries)
        mock_get_trends.side_effect = RetryableError("Persistent error")

        # Instantiate fallback (using default seed for predictability)
        fallback_source = SyntheticTrendSource(seed=0)
        adapter = GoogleTrendsAdapter(geo="US", fallback_source=fallback_source)
        
        signals = adapter.fetch()

        # Verify trendspy.get_trends was called max_retries + 1 times (3+1=4 times with default max_retries=3 in decorator)
        assert mock_get_trends.call_count == 4
        expected_query = os.environ.get("GOOGLE_TRENDS_QUERY", "trending searches")
        mock_get_trends.assert_called_with(query=expected_query, geo="US")

        # Verify the returned signals are from the synthetic source
        assert len(signals) == 10 # SyntheticTrendSource returns 10 signals
        assert all(isinstance(s, TrendSignal) for s in signals)
        assert signals[0].source == "synthetic"
        assert signals[0].keyword == "ai_automation"
