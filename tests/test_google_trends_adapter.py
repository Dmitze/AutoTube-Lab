"""Tests for GoogleTrendsAdapter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
import trendspyg # Import for mocking purposes

from modules.adapters.base import TrendSourceAdapter
from modules.adapters.errors import RetryableError # Import for simulating failures
from ytaimbot_ml.schemas import TrendSignal


# Mock RSS data for trendspyg.download_google_trends_rss
MOCK_RSS_FEED = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:ht="http://purl.org/rss/1.0/modules/slash/">
<channel>
    <title>Google Trends: Trending Searches</title>
    <link>https://trends.google.com/trends/trendingsearches/daily</link>
    <item>
        <title>Trend 1 Keyword</title>
        <ht:news_item_url>https://example.com/trend1</ht:news_item_url>
        <ht:news_item_title>News for Trend 1</ht:news_item_title>
        <ht:news_item_source>Source 1</ht:news_item_source>
        <ht:approx_traffic>1,000,000+</ht:approx_traffic>
        <pubDate>Tue, 02 Jun 2026 12:00:00 GMT</pubDate>
        <description>Description for Trend 1</description>
    </item>
    <item>
        <title>Trend 2 Keyword</title>
        <ht:news_item_url>https://example.com/trend2</ht:news_item_url>
        <ht:news_item_title>News for Trend 2</ht:news_item_title>
        <ht:news_item_source>Source 2</ht:news_item_source>
        <ht:approx_traffic>500,000+</ht:approx_traffic>
        <pubDate>Tue, 02 Jun 2026 13:00:00 GMT</pubDate>
        <description>Description for Trend 2</description>
    </item>
</channel>
</rss>
"""


class TestGoogleTrendsAdapter:
    """Tests for the GoogleTrendsAdapter."""

    @patch("trendspyg.download_google_trends_rss")
    def test_fetch_returns_trend_signals(self, mock_download_rss: MagicMock) -> None:
        """
        fetch() should call trendspyg and return a list of TrendSignal objects.
        """
        from modules.adapters.google_trends import GoogleTrendsAdapter

        mock_download_rss.return_value = MOCK_RSS_FEED
        adapter = GoogleTrendsAdapter(geo="US")
        
        signals = adapter.fetch()

        # Verify trendspyg was called with correct arguments
        mock_download_rss.assert_called_once_with(geo="US")

        # Verify the returned data is a list of TrendSignal
        assert isinstance(signals, list)
        assert len(signals) == 2
        assert all(isinstance(s, TrendSignal) for s in signals)

        # Verify content of the first TrendSignal
        signal1 = signals[0]
        assert signal1.trend_id == "trend-1-keyword"  # Should be slugified
        assert signal1.keyword == "Trend 1 Keyword"
        assert signal1.raw_score == 1_000_000
        assert signal1.source == "Google Trends"
        assert signal1.timestamp == "2026-06-02T12:00:00Z" # ISO-8601 UTC

        # Verify content of the second TrendSignal
        signal2 = signals[1]
        assert signal2.trend_id == "trend-2-keyword"
        assert signal2.keyword == "Trend 2 Keyword"
        assert signal2.raw_score == 500_000
        assert signal2.source == "Google Trends"
        assert signal2.timestamp == "2026-06-02T13:00:00Z"
    
    @patch("trendspyg.download_google_trends_rss")
    @patch("time.sleep") # Mock time.sleep for backoff testing
    @patch("modules.adapters.retry.random.random", return_value=0.0) # Correctly mock random.random where it's used
    def test_fetch_retries_on_failure(self, mock_random: MagicMock, mock_sleep: MagicMock, mock_download_rss: MagicMock) -> None:
        """
        fetch() should retry on transient failures with exponential backoff and jitter.
        """
        from modules.adapters.google_trends import GoogleTrendsAdapter

        # Simulate transient failures then success
        mock_download_rss.side_effect = [
            RetryableError("Transient error"),
            RetryableError("Another transient error"),
            MOCK_RSS_FEED, # Success on third attempt
        ]

        adapter = GoogleTrendsAdapter(geo="US")
        
        signals = adapter.fetch()

        # Verify trendspyg was called 3 times
        assert mock_download_rss.call_count == 3
        mock_download_rss.assert_called_with(geo="US")

        # Expected sleep calls for max_retries=3, base_delay=2.0, jitter=True (but random is mocked to 0.0)
        # 1st retry delay: 2.0 * (1 + 0.0) = 2.0s
        # 2nd retry delay: 4.0 * (1 + 0.0) = 4.0s
        mock_sleep.assert_any_call(2.0)
        mock_sleep.assert_any_call(4.0)
        assert mock_sleep.call_count == 2

        # Verify success after retries
        assert len(signals) == 2
        assert signals[0].keyword == "Trend 1 Keyword"
