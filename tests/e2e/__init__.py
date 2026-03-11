"""E2E tests package — full pipeline tests.

All tests here:
- Run the complete pipeline end-to-end
- Use synthetic adapters (no real APIs)
- Validate PipelineResult shape and metrics
- Target runtime: < 10s per file
- Seed: always seed=42
"""
