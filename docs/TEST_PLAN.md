# Test Plan

This document outlines the testing strategy.

---

## 1. Scope

This test plan covers all modules in `src/ytaimbot_ml/`, `modules/`, and their integration via `Pipeline`.  External APIs are **never called** during tests — all network-dependent code is replaced by synthetic adapters.

---

## 2. Unit Test Strategy

- **Framework**: pytest ≥ 8.0
- **Runner**: `pytest -q --tb=short`
- **Determinism**: every test that involves randomness passes an explicit seed.
- **No network**: tests must not import `requests`, `httpx`, or any network library.

### 2.1 TrendAnalyzer (`tests/test_trend_analyzer.py`)

| Test | Description | Pass criterion |
|------|-------------|----------------|
| `test_pca_reduces_dimensions` | `fit_transform` output shape | shape == (n, n_components) |
| `test_scoring_returns_sorted` | `score_trends` output order | descending by score |
| `test_determinism` | same seed → same output | element-wise equality |
| `test_top5_overlap` | stability across seeds | overlap ≥ 80 % |
| `test_analyze_empty_signals` | edge case | returns [] |
| `test_analyze_single_signal` | edge case | returns 1 ranking |

### 2.2 BayesQualityFilter (`tests/test_bayes_filter.py`)

| Test | Description | Pass criterion |
|------|-------------|----------------|
| `test_bad_sample_detected` | high-badness features | P(bad) > 0.5 |
| `test_good_sample_passes` | low-badness features | P(bad) < 0.5 |
| `test_decide_bad_returns_fail` | decision field | decision == "fail" |
| `test_decide_good_returns_pass` | decision field | decision == "pass" |
| `test_precision_on_synthetic` | 50/50 synthetic split | precision ≥ 80 % |
| `test_determinism` | same input twice | identical output |
| `test_empty_features_uses_prior` | edge case | returns prior |

### 2.3 Pipeline Orchestrator (`tests/test_orchestrator.py`)

| Test | Description | Pass criterion |
|------|-------------|----------------|
| `test_dry_run_pipeline` | full stages, no publish | status == "ok" |
| `test_gate_blocks_bad_content` | compliance gate logic | p_bad > 0.5 with high prior |
| `test_no_publish_without_gate` | dry_run publish suppression | publisher.published == [] |
| `test_publish_called_when_not_dry_run` | non-dry-run publish | published count == passed count |
| `test_pipeline_run_id_auto_generated` | auto run_id | status == "ok" |

---

## 3. Integration Test Strategy

Integration tests use `SyntheticTrendSource` and `InMemoryStorage` to exercise the full pipeline without mocking internal calls.  They verify:

- All pipeline stages execute in the correct order.
- Artefacts are persisted to storage.
- The fail-closed compliance gate works end-to-end.

---

## 4. Acceptance Criteria

| Module | Coverage target |
|--------|----------------|
| `ytaimbot_ml` | ≥ 80 % |
| `modules` | ≥ 80 % |
| Overall | ≥ 80 % |

---

## 5. Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest -q --tb=short

# Run with coverage
pytest --cov=src --cov=modules --cov-report=term-missing
```
