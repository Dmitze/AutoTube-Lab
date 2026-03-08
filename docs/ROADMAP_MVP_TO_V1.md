# Roadmap: MVP to V1

> Детальний roadmap розробки YTAIMBot від skeleton до production-ready бота.
> Кожна фаза — окремий PR із чіткими acceptance criteria.

---

## ✅ Phase 0 — Skeleton (COMPLETED)

**Goal**: Runnable Python package with deterministic ML stubs and passing CI.
**Duration**: Week 1
**Status**: ✅ Done

- [x] pyproject.toml with build system and dev dependencies
- [x] src/ytaimbot_ml/ package (TrendAnalyzer, BayesQualityFilter, schemas)
- [x] modules/ backend (Pipeline orchestrator, base adapters, synthetic adapters)
- [x] tests/ suite (≥ 15 tests, pytest passing)
- [x] .github/workflows/ci.yml (Python 3.11 + 3.12)
- [x] Dockerfile + docker-compose.yml
- [x] Filled documentation stubs

---

## 🔜 Phase 1 — Real Trend Adapters (NEXT)

**Goal**: Replace SyntheticTrendSource with real Google Trends + YouTube data.
**Duration**: Week 2–3
**Key libraries**: trendspyg, google-api-python-client
**Learned from**: [YouTube Trending Analysis](https://aneshraj-d96.github.io/YouTube-Analysis/) — ML dashboard with regression models for YouTube metrics (see [COMPETITIVE_ANALYSIS_2025](COMPETITIVE_ANALYSIS_2025.md) §2.1)

### Tasks:
- [ ] modules/adapters/google_trends.py (trendspyg RSS → TrendSignal)
- [ ] modules/adapters/youtube_search.py (YouTube Data API v3 → TrendSignal)
- [ ] modules/adapters/retry.py (exponential backoff + jitter decorator)
- [ ] Composite adapter: merge Google Trends + YouTube signals
- [ ] Integration tests with mocked HTTP responses
- [ ] ADR-0003: trendspyg instead of dead pytrends

### Acceptance:
- [ ] Both adapters implement TrendSourceAdapter
- [ ] Pipeline runs with real adapters (env vars set) or falls back to synthetic
- [ ] No network calls in tests
- [ ] Retry decorator handles 429/500 errors

---

## 📝 Phase 2 — Content Generation

**Goal**: Generate video scripts + voice from trending topics.
**Duration**: Week 4–5
**Key libraries**: edge-tts, Coqui TTS, Ollama (httpx)
**Learned from**: MoneyPrinter (Edge-TTS integration), ShortGPT (script templates)

### Tasks:
- [ ] modules/adapters/tts_edge.py (Edge-TTS — primary, free)
- [ ] modules/adapters/tts_local.py (Coqui TTS — local fallback for UA locality)
- [ ] modules/adapters/llm_local.py (Ollama HTTP adapter for script generation)
- [ ] src/ytaimbot_ml/content/generator.py (script template engine)
- [ ] src/ytaimbot_ml/content/templates/ (prompt templates for different niches)
- [ ] Token budget guard (max tokens per request)
- [ ] ADR-0004: Edge-TTS primary, Coqui fallback

### Acceptance:
- [ ] Script generation works with Ollama locally
- [ ] TTS produces audio files (.mp3/.wav)
- [ ] Fallback chain: Edge-TTS → Coqui TTS → error
- [ ] Works offline (Ollama + Coqui)

---

## 🎬 Phase 3 — Video Assembly + SEO

**Goal**: Compose final videos + optimize metadata for YouTube.
**Duration**: Week 6–7
**Key libraries**: MoviePy, FFmpeg, Pillow
**Learned from**: MoneyPrinter (MoviePy workflow), Viral-Faceless-Shorts-Generator (Docker+FFmpeg)

### Tasks:
- [ ] modules/video/assembler.py (audio + images → mp4 via MoviePy)
- [ ] modules/video/thumbnail.py (Pillow thumbnail generator 1280x720)
- [ ] modules/video/subtitles.py (SRT generation + burn-in)
- [ ] src/ytaimbot_ml/seo/optimizer.py (keyword expansion via autocomplete)
- [ ] src/ytaimbot_ml/seo/title_generator.py (CTR-optimized titles)
- [ ] ADR-0005: MoviePy for video assembly

### Acceptance:
- [ ] Produces valid 1080p mp4 with audio + subtitles
- [ ] Thumbnail is 1280x720 with readable text
- [ ] SEO optimizer generates ≥ 10 related keywords
- [ ] All without external API calls (free tools only)

---

## 🚀 Phase 4 — Publishing Pipeline

**Goal**: Upload videos to YouTube with compliance gates.
**Duration**: Week 8–9
**Key libraries**: google-api-python-client, google-auth
**Learned from**: AI-Video-Pipeline (AI disclosure), MoneyPrinter (upload flow)

### Tasks:
- [ ] modules/adapters/youtube_publisher.py (upload as unlisted)
- [ ] modules/adapters/youtube_auth.py (OAuth2 flow)
- [ ] AI content disclosure in metadata (learned from AI-Video-Pipeline)
- [ ] Rate-limit aware scheduler (max 1 upload per hour)
- [ ] Integration: Pipeline → generate → gate → upload (full loop)
- [ ] Manual review dashboard (simple CLI for first 50 videos)

### Acceptance:
- [ ] Videos upload as UNLISTED
- [ ] AI disclosure flag set in metadata
- [ ] Compliance gate blocks upload if BayesFilter score > threshold
- [ ] First 50 videos require manual approval
- [ ] Scheduler respects YouTube rate limits

---

## 📊 Phase 5 — Metrics Feedback Loop

**Goal**: Learn from video performance to improve future content.
**Duration**: Week 10–12
**Key libraries**: google-api-python-client (Analytics), SQLite/Postgres
**Learned from**: CrewAI (agent feedback), YouTube Trending Analysis (regression models)

### Tasks:
- [ ] modules/metrics_collector.py (YouTube Analytics API → MetricsSnapshot)
- [ ] Storage: extend SQLite schema for metrics (views, CTR, retention, RPM)
- [ ] src/ytaimbot_ml/feedback/scorer.py (adjust trend scores based on actual performance)
- [ ] A/B testing framework: compare title/thumbnail variants
- [ ] Weekly report generator (markdown output)
- [ ] Evaluate CrewAI vs custom Pipeline (ADR-0006)

### Acceptance:
- [ ] Metrics collected within 48h of upload
- [ ] Trend scores adjusted based on real CTR/views
- [ ] Weekly report shows top/bottom performing topics
- [ ] Decision on CrewAI documented in ADR

---

## 🧠 Phase 6 — RL Learner + Advanced

**Goal**: Autonomous niche selection and content optimization.
**Duration**: Week 13–16
**Key libraries**: PyTorch, Open-Sora (optional)

### Tasks:
- [ ] Multi-armed bandit for niche selection (Thompson Sampling)
- [ ] Reward signal: RPM × views × retention
- [ ] Online training loop with safety bounds
- [ ] Open-Sora integration evaluation (needs GPU budget)
- [ ] Drift detection for trend model

### Acceptance:
- [ ] Bandit improves niche selection over random by ≥ 20%
- [ ] Safety bounds prevent catastrophic niche switches
- [ ] Training loop runs without human intervention

---

## Timeline Summary

| Phase | Duration | Key Deliverable | Status |
|-------|----------|----------------|--------|
| 0 | Week 1 | Python skeleton + CI | ✅ Done |
| 1 | Week 2–3 | Real trend data | 🔜 Next |
| 2 | Week 4–5 | Voice + scripts | ⬜ Planned |
| 3 | Week 6–7 | Video + SEO | ⬜ Planned |
| 4 | Week 8–9 | YouTube upload | ⬜ Planned |
| 5 | Week 10–12 | Metrics + feedback | ⬜ Planned |
| 6 | Week 13–16 | RL learner | ⬜ Planned |

**Target**: First autonomous upload by Week 9 (~2 months from start).
**Revenue target**: $5k/month by Month 4–6.

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
