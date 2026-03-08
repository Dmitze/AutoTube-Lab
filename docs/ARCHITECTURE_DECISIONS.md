# Architecture Decisions (ADR log)

> Кожне рішення — коротко: контекст, рішення, наслідки.

## ADR-0001: Repo structure separation
**Context:** змішування ML/Backend/DevOps ускладнює тестування.  
**Decision:** ML в `src/ytaimbot_ml/`, backend в `modules/`, docs/tests окремо.  
**Consequences:** чисті межі, легше писати deterministic tests.

## ADR-0002: No network calls in unit tests
**Context:** flaky tests, rate limits, cost.  
**Decision:** всі інтеграції — через adapters + mocks.  
**Consequences:** треба підтримувати fake datasets/fixtures.

## ADR-0003: Use trendspyg instead of pytrends
**Context:** pytrends (GeneralMills/pytrends) is archived and no longer maintained. Google Trends scraping breaks regularly.  
**Decision:** Use trendspyg (RSS-based, async, actively maintained) as primary Google Trends adapter.  
**Consequences:** RSS-based approach is less feature-rich but more reliable. SerpApi as paid fallback.

## ADR-0004: Edge-TTS primary, Coqui TTS fallback
**Context:** Need free TTS for budget-first approach. ElevenLabs is paid ($5+/month).  
**Decision:** Edge-TTS (free Microsoft Azure Neural Voices) as primary. Coqui TTS (open-source, local) as fallback for UA locality / network issues.  
**Consequences:** Edge-TTS is unofficial API (risk of blocking). Coqui needs more CPU but works offline.

## ADR-0005: MoviePy for video assembly
**Context:** Need Python video editing. Options: MoviePy, OpenCV, FFmpeg direct, Remotion.  
**Decision:** MoviePy — mature, well-documented, FFmpeg-based, good Python API.  
**Consequences:** Requires FFmpeg system binary (Docker ensures this). Sufficient for faceless videos.

## ADR-0006: Evaluate CrewAI vs custom Pipeline at Phase 5
**Context:** Our custom Pipeline class works for MVP. CrewAI offers more advanced multi-agent orchestration.  
**Decision:** Defer decision to Phase 5 when we have real metrics. Evaluate if CrewAI's benefits justify the dependency.  
**Consequences:** Keep Pipeline simple for now. Document evaluation criteria.