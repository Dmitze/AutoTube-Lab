"""Unit tests package — fast tests with no I/O.

All tests here:
- Run without network/filesystem
- No mocking needed (pure functions)
- Target runtime: < 100ms per file
- Seed: always use seed=42 for determinism
"""
