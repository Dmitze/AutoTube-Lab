"""Integration tests package — tests with mocked I/O.

All tests here:
- Mock all network calls (httpx, groq, trendspy, YouTube API)
- Mock all filesystem calls (tmp_path fixture)
- No real API keys required
- Target runtime: < 1s per file
"""
