# ADR-0001: Adapter Pattern (Ports & Adapters / Hexagonal Architecture)

**Date:** 2026-01-W1  
**Status:** ✅ Accepted  
**Deciders:** Project owner

## Context

The pipeline needs to integrate with multiple external services: Google Trends, YouTube API, LLMs (Groq/Ollama), TTS engines (Edge TTS/Coqui), and video tools (FFmpeg/MoviePy). Each has different APIs, quotas, and failure modes.

## Decision

All I/O goes through Abstract Base Classes (ABCs) defined in `modules/adapters/base.py`. Concrete implementations are swappable at runtime via factory functions and environment variables.

```
TrendSourceAdapter  → SyntheticTrendSource | GoogleTrendsTrendSource | YouTubeSearchTrendSource | CompositeTrendSource
LLMAdapter          → GroqAdapter | OllamaAdapter
TTSAdapter          → EdgeTTSAdapter | CoquiTTSAdapter
PublisherAdapter    → StubPublisher | YouTubeUploader
StorageAdapter      → InMemoryStorage | SQLiteStorage
```

## Consequences

**Good:**
- Tests use synthetic/in-memory adapters — no real API calls ever
- Swap implementations without changing pipeline logic
- Each adapter has a single responsibility

**Bad:**
- More files/classes to maintain
- Adapter interface must be stable (breaking changes = update all implementations)
