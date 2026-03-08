# Test Documentation for YTAIMBot

## Overview

This document describes the testing strategy for the YTAIMBot project.

For the full test plan see [`docs/TEST_PLAN.md`](../docs/TEST_PLAN.md).

---

## Quick Start

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest -q --tb=short

# Run with coverage report
pytest --cov=src --cov=modules --cov-report=term-missing
```

---

## Test Suite Structure

```
tests/
├── conftest.py            # Shared fixtures (rng, synthetic_trends, …)
├── test_trend_analyzer.py # Unit tests for TrendAnalyzer
├── test_bayes_filter.py   # Unit tests for BayesQualityFilter
└── test_orchestrator.py   # Integration tests for Pipeline
```

---

## Key Principles

- **No network calls** — all adapters are synthetic or in-memory.
- **Deterministic** — every test that involves randomness uses an explicit seed.
- **Python 3.11+** — tests run on 3.11 and 3.12 in CI.
- **pytest** ≥ 8.0 with `pytest-cov` ≥ 4.0.

---

## CI

Tests run automatically on every push and pull request via
`.github/workflows/ci.yml` (GitHub Actions, `ubuntu-latest`,
Python 3.11 + 3.12, `actions/checkout@v4` + `actions/setup-python@v5`).

