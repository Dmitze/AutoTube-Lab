# Roadmap: MVP to V1

This document outlines the roadmap from MVP to V1.

---

## Phase 0 — Skeleton (this PR)

**Goal**: Runnable Python package with deterministic ML stubs and passing CI.

- [x] `pyproject.toml` with build system and dev dependencies
- [x] `src/ytaimbot_ml/` package (TrendAnalyzer, BayesQualityFilter, schemas)
- [x] `modules/` backend (Pipeline orchestrator, base adapters, synthetic adapters)
- [x] `tests/` suite (≥ 15 tests, pytest passing)
- [x] `.github/workflows/ci.yml` (Python 3.11 + 3.12)
- [x] `Dockerfile` + `docker-compose.yml`
- [x] Filled documentation

---

## Phase 1 — Real Trend Adapters

**Goal**: Replace `SyntheticTrendSource` with real data sources.

- [ ] `modules/adapters/google_trends.py` — pytrends integration
- [ ] `modules/adapters/youtube.py` — YouTube Data API v3 (quota-aware)
- [ ] Exponential-backoff retry decorator
- [ ] Integration tests with mocked HTTP responses (no real network)

---

## Phase 2 — Content Generation Stubs

**Goal**: Generate real video scripts via local LLM.

- [ ] `src/ytaimbot_ml/content/generator.py` — Ollama / OpenAI stub
- [ ] ContentPlan enriched with full script outline
- [ ] Token budget guard

---

## Phase 3 — SEO Optimiser

**Goal**: Enhance keyword lists with search-volume proxies.

- [ ] `src/ytaimbot_ml/seo/optimizer.py`
- [ ] Keyword expansion using Google Autocomplete (free, no key)
- [ ] Keyword deduplication and relevance scoring

---

## Phase 4 — Publishing Pipeline

**Goal**: Upload videos to YouTube automatically.

- [ ] `modules/adapters/youtube_publisher.py` — YouTube upload API
- [ ] Unlisted-first upload strategy (FR-04)
- [ ] Thumbnail generation stub
- [ ] Rate-limit-aware scheduler

---

## Phase 5 — Metrics Feedback Loop

**Goal**: Collect performance data and improve trend scoring.

- [ ] `modules/metrics_collector.py` — YouTube Analytics API
- [ ] Feedback store (SQLite / Postgres)
- [ ] Score adjustment based on view/click-through rate

---

## Phase 6 — RL Learner

**Goal**: Continuously improve niche selection using reinforcement learning.

- [ ] Multi-armed bandit or contextual bandit for niche selection
- [ ] Reward signal: monetisation metrics (RPM, views)
- [ ] Online training loop with safety bounds
