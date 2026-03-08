# External Dependencies Integration Plan

> Технічний план інтеграції бібліотек з аналізу конкурентів у YTAIMBot pipeline.

## 1. Integration phases

### Phase 1 — Trend Adapters (Next Sprint)

| Library | Purpose | Target file | Interface | Tests |
|---------|---------|------------|-----------|-------|
| trendspyg | Google Trends RSS source | modules/adapters/google_trends.py | TrendSourceAdapter | tests/test_google_trends_adapter.py |
| youtube-data-api (google-api-python-client) | YouTube search signals | modules/adapters/youtube_search.py | TrendSourceAdapter | tests/test_youtube_search_adapter.py |

### Phase 2 — Content Generation

| Library | Purpose | Target file | Interface | Tests |
|---------|---------|------------|-----------|-------|
| edge-tts | Free TTS (primary) | modules/adapters/tts_edge.py | TTSAdapter (ABC) | tests/test_tts_adapter.py |
| coqui-ai/TTS | Local TTS fallback | modules/adapters/tts_local.py | TTSAdapter (ABC) | tests/test_tts_local_adapter.py |
| ollama (via HTTP) | Local LLM for scripts | modules/adapters/llm_local.py | LLMAdapter (ABC) | tests/test_llm_adapter.py |

### Phase 3 — Video Assembly

| Library | Purpose | Target file | Interface | Tests |
|---------|---------|------------|-----------|-------|
| moviepy | Video editing/composition | modules/video/assembler.py | VideoAssembler | tests/test_video_assembler.py |
| Pillow | Thumbnail generation | modules/video/thumbnail.py | ThumbnailGenerator | tests/test_thumbnail.py |
| FFmpeg (subprocess) | Final render/transcode | called by MoviePy | N/A | N/A |

### Phase 4 — Publishing

| Library | Purpose | Target file | Interface | Tests |
|---------|---------|------------|-----------|-------|
| google-api-python-client | YouTube upload | modules/adapters/youtube_publisher.py | PublisherAdapter | tests/test_publisher.py |
| google-auth | OAuth2 for YouTube | modules/adapters/youtube_auth.py | N/A | tests/test_youtube_auth.py |

### Phase 5+ — Advanced

| Library | Purpose | Target file | When |
|---------|---------|------------|------|
| crewai | Multi-agent orchestration | Evaluate vs custom Pipeline | Phase 5 |
| langchain | LLM orchestration for complex scripts | modules/adapters/llm_chain.py | Phase 5 |
| Open-Sora | AI video generation | modules/video/ai_generator.py | Phase 6+ (needs GPU) |
| pytorch | PPO/RL learner | src/ytaimbot_ml/learner.py | Phase 6 |

## 2. New abstract interfaces needed

```python
# modules/adapters/base.py — extend with:

class TTSAdapter(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice: str, output_path: str) -> str: ...

class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text from prompt. Raises LLMError on timeout/connection failure."""
        ...

class VideoAssembler(ABC):
    @abstractmethod
    def assemble(self, script: str, audio_path: str, output_path: str) -> str: ...

class ThumbnailGenerator(ABC):
    @abstractmethod
    def generate(self, title: str, output_path: str) -> str: ...
```

## 3. pyproject.toml updates (per phase)

- **Phase 1:** add `trendspyg`, `google-api-python-client`
- **Phase 2:** add `edge-tts`, `TTS` (coqui), `httpx` (for ollama)
- **Phase 3:** add `moviepy`, `Pillow`
- **Phase 4:** add `google-auth`, `google-auth-oauthlib`

## 4. Architecture Decision Records (new ADRs)

- ADR-0003: Use trendspyg instead of pytrends (pytrends is archived/dead)
- ADR-0004: Edge-TTS as primary TTS with Coqui TTS as local fallback
- ADR-0005: MoviePy for video assembly (mature, well-documented, FFmpeg-based)
- ADR-0006: Evaluate CrewAI vs custom Pipeline at Phase 5 milestone

## 5. Risk matrix for external dependencies

| Dependency | Risk | Probability | Mitigation |
|-----------|------|------------|------------|
| trendspyg | RSS feed changes | Medium | SerpApi fallback, cache layer |
| edge-tts | Microsoft blocks unofficial API | Medium | Coqui TTS local fallback |
| YouTube Data API | Quota exceeded | High | Exponential backoff, daily budget tracking |
| MoviePy | Dependency on FFmpeg system binary | Low | Docker ensures FFmpeg present |
| Coqui TTS | Requires GPU for quality | Medium | CPU mode acceptable for MVP, GPU on Hetzner later |
| ollama | Model download size (4-7GB) | Low | Pre-pull in Docker build |
