"""Tests for YouTubeSearchAdapter."""

from __future__ import annotations

import os
import certifi
os.environ["HTTPLIB2_CA_CERTS"] = certifi.where()

from unittest.mock import MagicMock, patch

import pytest

# No direct import of googleapiclient.discovery here to avoid the httplib2 issue
from modules.adapters.base import TrendSourceAdapter
from ytaimbot_ml.schemas import TrendSignal


# Mock YouTube API response for search().list().execute()
MOCK_YOUTUBE_API_RESPONSE = {
    "kind": "youtube#searchListResponse",
    "etag": "etag_value",
    "nextPageToken": "CAUQAA",
    "regionCode": "US",
    "pageInfo": {"totalResults": 1000000, "resultsPerPage": 5},
    "items": [
        {
            "kind": "youtube#searchResult",
            "etag": "etag1",
            "id": {"kind": "youtube#video", "videoId": "video1"},
            "snippet": {
                "publishedAt": "2026-06-01T10:00:00Z",
                "channelId": "channel1",
                "title": "YouTube Trend 1: AI Future",
                "description": "Description for video 1",
                "thumbnails": {"default": {"url": "thumbnail1.jpg"}},
                "channelTitle": "Channel 1",
                "liveBroadcastContent": "none",
                "publishTime": "2026-06-01T10:00:00Z",
            },
        },
        {
            "kind": "youtube#searchResult",
            "etag": "etag2",
            "id": {"kind": "youtube#video", "videoId": "video2"},
            "snippet": {
                "publishedAt": "2026-06-01T11:00:00Z",
                "channelId": "channel2",
                "title": "Top Tech Trends 2026",
                "description": "Description for video 2",
                "thumbnails": {"default": {"url": "thumbnail2.jpg"}},
                "channelTitle": "Channel 2",
                "liveBroadcastContent": "none",
                "publishTime": "2026-06-01T11:00:00Z",
            },
        },
    ],
}


class TestYouTubeSearchAdapter:
    """Tests for the YouTubeSearchAdapter."""

    # Mock googleapiclient.discovery.build directly to avoid httplib2 import
    @patch("googleapiclient.discovery.build")
    @patch("os.environ.get", return_value="MOCK_API_KEY") # Mock API key from env var
    def test_fetch_returns_trend_signals(
        self, mock_env_get: MagicMock, mock_build: MagicMock
    ) -> None:
        """
        fetch() should call YouTube API and return a list of TrendSignal objects.
        """
        # Configure mock_build to return a mock service that can be called
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.search().list().execute.return_value = MOCK_YOUTUBE_API_RESPONSE

        # Import YouTubeSearchAdapter inside the test function
        # to ensure mocking is set up before its module is loaded
        from modules.adapters.youtube_search import YouTubeSearchAdapter

        adapter = YouTubeSearchAdapter() # No geo param for YouTube
        signals = adapter.fetch()

        # Verify googleapiclient.discovery.build was called with correct arguments
        mock_build.assert_called_once_with("youtube", "v3", developerKey="MOCK_API_KEY")

        # Verify search().list().execute() was called with correct arguments
        mock_service.search().list.assert_called_once_with(
            part="snippet", type="video", order="viewCount", q="", maxResults=50
        )

        # Verify the returned data is a list of TrendSignal
        assert isinstance(signals, list)
        assert len(signals) == 2
        assert all(isinstance(s, TrendSignal) for s in signals)

        # Verify content of the first TrendSignal
        signal1 = signals[0]
        assert signal1.trend_id == "video1"
        assert signal1.keyword == "YouTube Trend 1: AI Future"
        assert signal1.raw_score == 0 # YouTube API does not provide a direct 'score' for search results
        assert signal1.source == "YouTube Search"
        assert signal1.timestamp == "2026-06-01T10:00:00Z"

        # Verify content of the second TrendSignal
        signal2 = signals[1]
        assert signal2.trend_id == "video2"
        assert signal2.keyword == "Top Tech Trends 2026"
        assert signal2.raw_score == 0
        assert signal2.source == "YouTube Search"
        assert signal2.timestamp == "2026-06-01T11:00:00Z"
