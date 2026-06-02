"""Google Trends adapter for fetching trend signals."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import trendspyg
from modules.adapters.base import TrendSourceAdapter
from ytaimbot_ml.schemas import TrendSignal # Moved outside TYPE_CHECKING block


class GoogleTrendsAdapter(TrendSourceAdapter):
    """Fetches trending searches from Google Trends RSS feed."""

    # Google Trends specific namespace for custom elements
    _HT_NAMESPACE = "{http://purl.org/rss/1.0/modules/slash/}"

    def __init__(self, geo: str = "US") -> None:
        """Initialize the GoogleTrendsAdapter.

        Parameters
        ----------
        geo:
            Geographical location for trend data (e.g., "US", "UA").
        """
        self._geo = geo

    def fetch(self) -> list[TrendSignal]:
        """Return a list of TrendSignal objects.

        Complexity: O(N) where N is the number of items in the RSS feed.
        """
        rss_feed = trendspyg.download_google_trends_rss(geo=self._geo)
        root = ET.fromstring(rss_feed)

        signals: list[TrendSignal] = []
        for item in root.findall(".//item"):
            title_element = item.find("title")
            approx_traffic_element = item.find(f"{self._HT_NAMESPACE}approx_traffic")
            pub_date_element = item.find("pubDate")

            if title_element is None or approx_traffic_element is None or pub_date_element is None:
                continue  # Skip items that don't have all required data

            keyword = title_element.text or ""
            
            # Extract raw_score, removing '+' and commas
            raw_score_str = re.sub(r"[+,]", "", approx_traffic_element.text or "0")
            raw_score = int(raw_score_str)

            # Parse pubDate and format to ISO-8601 UTC
            pub_date_str = pub_date_element.text
            # Example: 'Tue, 02 Jun 2026 12:00:00 GMT'
            dt_object = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=timezone.utc)
            timestamp = dt_object.isoformat(timespec="seconds").replace("+00:00", "Z")

            # Generate trend_id (slugify)
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