# ADR-0003: trendspy over pytrends for Google Trends

**Date:** 2026-01-W2  
**Status:** ✅ Accepted

## Context

Need to fetch Google Trends data without authentication. Two options:
- `pytrends` — widely known, but uses unofficial API, frequently breaks
- `trendspy` — newer library, uses RSS feed (more stable), actively maintained

## Decision

Use `trendspy >= 0.1.4` (PyPI: `trendspy`).

```python
import trendspy
trends = trendspy.Trends()
data = trends.trending_now(geo="US")
```

## Consequences

**Good:**
- RSS-based → more stable than unofficial API scraping
- No authentication required
- Handles geo parameter cleanly

**Bad:**
- Smaller community than pytrends
- RSS may change format without notice → need `_extract_keyword()` fallback parser

**Fallback:**
If trendspy fails → `SyntheticTrendSource` (never blocks pipeline)
