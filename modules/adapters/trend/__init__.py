"""Phase 1 — Trend adapters sub-package.

Re-exports existing trend adapters and provides the build_trend_source factory.

Adapters
--------
GoogleTrendsTrendSource  : trendspy RSS → TrendSignal[]
YouTubeSearchTrendSource : YouTube Data API v3 → TrendSignal[]
CompositeTrendSource     : K-way merge of multiple sources

Factory
-------
build_trend_source(config) → TrendSourceAdapter
    Auto-selects the best adapter based on available env vars.
    Priority: Composite (YouTube+Google) → GoogleTrends → Synthetic

Status: ✅ Phase 1 complete (T-016–T-080)
"""
from __future__ import annotations

import logging
from typing import Any

from modules.adapters.composite import CompositeTrendSource
from modules.adapters.google_trends import GoogleTrendsTrendSource
from modules.adapters.youtube_search import YouTubeSearchTrendSource

logger = logging.getLogger(__name__)

__all__ = [
    "GoogleTrendsTrendSource",
    "YouTubeSearchTrendSource",
    "CompositeTrendSource",
    "build_trend_source",
]


def build_trend_source(config: dict[str, Any]):
    """Auto-select and build the best available trend source adapter.

    Selection priority (T-069):
    1. CompositeTrendSource  — when YOUTUBE_API_KEY is set (merges YT + Google)
    2. GoogleTrendsTrendSource — when no YouTube key but trendspy is available
    3. SyntheticTrendSource  — deterministic fallback (always works)

    Parameters
    ----------
    config:
        Application configuration dict (keys from env vars).

    Returns
    -------
    TrendSourceAdapter
        Ready-to-use adapter instance.

    Complexity: O(1) — factory selection.

    Example
    -------
    >>> source = build_trend_source({"GOOGLE_TRENDS_GEO": "US"})
    >>> hasattr(source, "fetch")
    True
    """
    from modules.adapters.base import TrendSourceAdapter  # noqa: PLC0415

    youtube_key: str | None = config.get("YOUTUBE_API_KEY") or None
    geo: str = config.get("GOOGLE_TRENDS_GEO", "US")
    ttl: int = int(config.get("TREND_CACHE_TTL", 900))

    # Parse adapter weights (e.g. "1.0,1.5")
    weights_raw: str = config.get("ADAPTER_WEIGHTS", "1.0,1.0")
    try:
        weights = [float(w) for w in weights_raw.split(",")]
    except ValueError:
        weights = [1.0, 1.0]
    yt_weight = weights[0] if len(weights) > 0 else 1.0
    gt_weight = weights[1] if len(weights) > 1 else 1.0

    if youtube_key:
        logger.info(
            "build_trend_source: using CompositeTrendSource "
            "(YouTube + Google Trends, cache TTL=%ds)", ttl
        )
        yt_source = YouTubeSearchTrendSource(api_key=youtube_key)
        gt_source = GoogleTrendsTrendSource(geo=geo)
        return CompositeTrendSource(
            adapters=[yt_source, gt_source],
            weights=[yt_weight, gt_weight],
            cache_ttl=ttl,
        )

    logger.info(
        "build_trend_source: YOUTUBE_API_KEY not set — "
        "using GoogleTrendsTrendSource (geo=%s)", geo
    )
    try:
        return GoogleTrendsTrendSource(geo=geo)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "build_trend_source: GoogleTrends init failed (%s) — "
            "falling back to SyntheticTrendSource", exc
        )

    # Always-works fallback
    from modules.adapters.synthetic import SyntheticTrendSource  # noqa: PLC0415
    return SyntheticTrendSource()

