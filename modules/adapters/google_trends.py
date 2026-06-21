"""Google Trends adapter for fetching trend signals."""

from __future__ import annotations

import re
import os
import xml.etree.ElementTree as ET # No longer needed for trendspy DataFrame
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import trendspy
import pandas as pd # Import pandas for DataFrame handling
from modules.adapters.base import TrendSourceAdapter
from modules.adapters.errors import RetryableError
from modules.adapters.retry import exponential_backoff
from ytaimbot_ml.schemas import TrendSignal


class GoogleTrendsAdapter(TrendSourceAdapter):
    """Fetches trending searches from Google Trends using the `trendspy` library.

    This adapter uses `trendspy.Trends().get_trends()` to fetch trending searches and
    converts the resulting Pandas DataFrame into a list of `TrendSignal` objects.
    """

    def __init__(self, geo: str = "US", fallback_source: TrendSourceAdapter | None = None, seed: int = 42) -> None:
        """Initialize the GoogleTrendsAdapter.

        Parameters
        ----------
        geo:
            Geographical location for trend data (e.g., "US", "UA").
        fallback_source:
            Optional TrendSourceAdapter to use if primary fetch fails persistently.
        seed:
            Integer seed for reproducibility, passed to underlying components if any.
        """
        self._geo = geo
        self._fallback_source = fallback_source
        self._seed = seed # Store seed if needed for internal components.
        # trendspy.Trends().get_trends requires a query. Since the original intent was general trends,
        # we'll use a broad query or rely on the library's default if it exists.
        # For now, a generic "trending searches" query will be used, though trendspy
        # focuses on specific queries. This might need further discussion.
        self._query = os.environ.get("GOOGLE_TRENDS_QUERY", "trending searches")


    @exponential_backoff(max_retries=3, base_delay=2.0, jitter=True, seed=42) # Added seed for determinism
    def _fetch_with_retries(self) -> list[TrendSignal]:
        """Internal method for fetching trends with retries, without fallback.

        This method calls `trendspy.Trends().get_trends()` and parses the DataFrame result.
        """
        # trendspy.Trends().get_trends requires a query, but the original GoogleTrendsAdapter
        # was designed for general trending searches without a specific query.
        # We will use a general query.
        client = trendspy.Trends()
        df = client.get_trends(query=self._query, geo=self._geo)

        signals: list[TrendSignal] = []
        # Iterate over DataFrame rows and convert to TrendSignal
        for _, row in df.iterrows():
            # trendspy does not provide a direct 'raw_score' (approx_traffic)
            # Assigning 0 for now, similar to YouTubeSearchAdapter if direct score is unavailable.
            raw_score = 0
            
            # Use 'search_term' from DataFrame as keyword
            keyword = row["search_term"]
            
            # 'date' column contains datetime objects
            # Convert to ISO-8601 UTC string
            # Check if 'date' column exists, otherwise use current time as fallback
            if "date" in row and pd.notna(row["date"]):
                dt_object = row["date"].replace(tzinfo=timezone.utc)
                timestamp = dt_object.isoformat(timespec="seconds").replace("+00:00", "Z")
            else:
                # Fallback to current UTC time if date is not available
                timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


            # Generate a unique trend_id from the keyword
            trend_id = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")
            
            signals.append(
                TrendSignal(
                    trend_id=trend_id,
                    keyword=keyword,
                    raw_score=raw_score,
                    source="Google Trends",
                    timestamp=timestamp,
                )
            )
        return signals

    def fetch(self) -> list[TrendSignal]:
        """Return a list of TrendSignal objects.

        Complexity: O(N) where N is the number of items returned by `trendspy.Trends().get_trends()`.
        """
        try:
            return self._fetch_with_retries()
        except RetryableError:
            if self._fallback_source:
                return self._fallback_source.fetch()
            raise
