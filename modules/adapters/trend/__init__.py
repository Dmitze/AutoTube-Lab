"""Phase 1 — Trend adapters sub-package.

Re-exports existing trend adapters for cleaner imports.

Adapters
--------
GoogleTrendsTrendSource  : trendspy RSS → TrendSignal[]
YouTubeSearchTrendSource : YouTube Data API v3 → TrendSignal[]
CompositeTrendSource     : K-way merge of multiple sources

Note: source files still live at modules/adapters/google_trends.py etc.
      This package provides grouped imports for Phase 2+ code.

Status: ✅ Phase 1 complete (T-016–T-080)
"""
from modules.adapters.composite import CompositeTrendSource
from modules.adapters.google_trends import GoogleTrendsTrendSource
from modules.adapters.youtube_search import YouTubeSearchTrendSource

__all__ = [
    "GoogleTrendsTrendSource",
    "YouTubeSearchTrendSource",
    "CompositeTrendSource",
]
