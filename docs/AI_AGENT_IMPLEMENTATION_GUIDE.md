# AI Agent Implementation Guide — YTAIMBot 2026

> Цей документ — головна інструкція для AI-агента. Читай його ПЕРЕД будь-якою імплементацією.
> Він пояснює ЩО будувати, в ЯКОМУ порядку, з ЯКИМИ бібліотеками, і з ЯКИМИ acceptance criteria.

## 0. Перш ніж починати

1. Прочитай docs/COMPETITIVE_ANALYSIS_2025.md — зрозумій ландшафт
2. Прочитай docs/EXTERNAL_DEPENDENCIES_INTEGRATION_PLAN.md — зрозумій залежності
3. Прочитай docs/ROADMAP_MVP_TO_V1.md — зрозумій порядок фаз
4. Прочитай docs/ARCHITECTURE_DATAFLOW.md — зрозумій pipeline
5. Перевір поточний код: src/ytaimbot_ml/, modules/, tests/

## 1. Конкретні завдання по фазах

### Phase 1: Real Trend Adapters (НАСТУПНИЙ СПРИНТ)

#### Task 1.1: Google Trends Adapter
- **File:** modules/adapters/google_trends.py
- **Library:** trendspyg (pip install trendspyg)
- **Interface:** implements TrendSourceAdapter from modules/adapters/base.py
- **Logic:**
  - fetch() → call trendspyg.download_google_trends_rss(geo='US')
  - Parse RSS results into list[TrendSignal]
  - Handle rate limits with exponential backoff (max 3 retries, base 2s, jitter)
  - Fallback to SyntheticTrendSource on failure
- **Tests:** tests/test_google_trends_adapter.py
  - Mock trendspyg responses (NO real network calls)
  - Test parse of RSS → TrendSignal
  - Test retry logic
  - Test fallback to synthetic
- **Acceptance:**
  - [ ] Implements TrendSourceAdapter
  - [ ] No network calls in tests
  - [ ] Handles rate limits gracefully
  - [ ] Falls back to synthetic on failure

#### Task 1.2: YouTube Search Adapter
- **File:** modules/adapters/youtube_search.py
- **Library:** google-api-python-client
- **Interface:** implements TrendSourceAdapter
- **Logic:**
  - fetch() → call YouTube Data API v3 search.list(part='snippet', type='video', order='viewCount')
  - Parse results into list[TrendSignal]
  - Respect quota: max 100 units/request, track daily usage
  - API key from env var YOUTUBE_API_KEY
- **Tests:** tests/test_youtube_search_adapter.py
  - Mock googleapiclient responses
  - Test parse → TrendSignal
  - Test quota tracking
- **Acceptance:**
  - [ ] Implements TrendSourceAdapter
  - [ ] API key only from env var
  - [ ] Quota tracking works
  - [ ] No network calls in tests

#### Task 1.3: Retry Decorator
- **File:** modules/adapters/retry.py
- **Logic:** exponential_backoff(max_retries=3, base_delay=2.0, jitter=True)
- **Tests:** tests/test_retry.py
  - Test backoff timing (mocked time.sleep)
  - Test max retries exceeded → raises
  - Test jitter adds randomness
- **Acceptance:**
  - [ ] Decorator works with any adapter
  - [ ] Deterministic with seed for jitter RNG

### Phase 2: Content Generation

#### Task 2.1: TTS Adapter (Edge-TTS)
- **File:** modules/adapters/tts_edge.py
- **Library:** edge-tts
- **Interface:** TTSAdapter (new ABC in base.py)
- **Logic:** async synthesize(text, voice='uk-UA-OstapNeural', output_path) → .mp3 file
- **Tests:** mock edge-tts communicate()
- **Acceptance:**
  - [ ] Async interface
  - [ ] Ukrainian voice support
  - [ ] Fallback-ready (can swap to Coqui)

#### Task 2.2: TTS Fallback (Coqui TTS)
- **File:** modules/adapters/tts_local.py
- **Library:** TTS (coqui-ai)
- **Interface:** TTSAdapter
- **Logic:** synthesize(text, model='tts_models/en/ljspeech/tacotron2-DDC', output_path) → .wav
- **Tests:** mock TTS.api
- **Acceptance:**
  - [ ] Works without internet
  - [ ] CPU mode for MVP

#### Task 2.3: LLM Adapter (Ollama)
- **File:** modules/adapters/llm_local.py
- **Library:** httpx (HTTP calls to localhost:11434)
- **Interface:** LLMAdapter (new ABC)
- **Logic:** generate(prompt, model='llama3', max_tokens=2000) → str
- **Tests:** mock httpx responses
- **Acceptance:**
  - [ ] Local-first (no cloud dependency)
  - [ ] Configurable model name

### Phase 3: Video Assembly

#### Task 3.1: Video Assembler
- **File:** modules/video/assembler.py
- **Library:** moviepy
- **Interface:** VideoAssembler (new ABC)
- **Logic:**
  - Take audio + background images/video → compose final video
  - Add subtitles (SRT → burn into video)
  - Target: 1080p, 30fps, mp4 (h264)
- **Learned from:** MoneyPrinter (moviepy workflow), ShortGPT (multi-scene)
- **Tests:** mock moviepy objects
- **Acceptance:**
  - [ ] Produces valid mp4
  - [ ] Configurable resolution/fps

#### Task 3.2: Thumbnail Generator
- **File:** modules/video/thumbnail.py
- **Library:** Pillow
- **Logic:**
  - Generate YouTube thumbnail: 1280x720, bold title text, gradient background
  - Configurable: font, colors, layout
- **Tests:** check output dimensions, file exists
- **Acceptance:**
  - [ ] 1280x720 output
  - [ ] Readable text

### Phase 4: Publishing

#### Task 4.1: YouTube Publisher
- **File:** modules/adapters/youtube_publisher.py
- **Library:** google-api-python-client
- **Interface:** PublisherAdapter
- **Logic:**
  - Upload video as UNLISTED first (compliance: first 50 videos)
  - Set metadata: title, description, tags, category
  - AI disclosure flag (learned from AI-Video-Pipeline)
  - Rate-limit aware
- **Tests:** mock YouTube API
- **Acceptance:**
  - [ ] Uploads as unlisted
  - [ ] Sets AI disclosure
  - [ ] Compliance gate check before upload

## 2. Patterns to follow (learned from competitors)

### From MoneyPrinter:
- Simple linear pipeline: topic → script → audio → video → upload
- Use Edge-TTS for free voice generation
- MoviePy for video composition

### From ShortGPT:
- Modular agent architecture with clear roles
- Each stage is independently testable
- Support for multiple video formats (Shorts + Long)

### From AI-Video-Pipeline:
- AI content disclosure in YouTube metadata
- Compliance-first approach to publishing

### From CrewAI:
- Role-based agent system (TrendAgent, ContentAgent, SEOAgent)
- Task delegation with dependencies
- Evaluate for Phase 5 replacement of our Pipeline

## 3. Hard Rules (NEVER BREAK)

1. NO external network calls in unit tests
2. ALL ML must be deterministic (seed/RNG)
3. Secrets ONLY via env vars
4. Compliance gate MUST pass before publish
5. First 50 videos: unlisted-first + manual review
6. Code only in: src/ytaimbot_ml/, modules/, tests/, docs/
7. Every public function: docstring + types + Big-O

## 4. Technology Stack Summary

| Layer | Technology | Phase |
|-------|-----------|-------|
| ML/Analysis | numpy, scikit-learn, scipy | ✅ Phase 0 |
| Trend Source | trendspyg, YouTube Data API | Phase 1 |
| Voice | edge-tts (primary), Coqui TTS (fallback) | Phase 2 |
| LLM | Ollama (local), OpenAI (optional paid) | Phase 2 |
| Video | MoviePy, FFmpeg, Pillow | Phase 3 |
| Publishing | google-api-python-client, google-auth | Phase 4 |
| Orchestration | Custom Pipeline → evaluate CrewAI | Phase 5 |
| RL/Learning | PyTorch (bandit/PPO) | Phase 6 |
| Infra | Docker, docker-compose, GitHub Actions | ✅ Phase 0 |
| Deploy | Hetzner CX22 (4GB RAM), local-first | Phase 4+ |
