# ADR-0004: Groq API (primary) + Ollama (fallback) for LLM

**Date:** 2026-01-W3  
**Status:** ✅ Accepted

## Context

Script generation requires an LLM. Options:
1. OpenAI GPT-4 — expensive, ~$0.01/1k tokens
2. Groq API — free tier (14k req/day), llama-3.1-8b-instant
3. Ollama local — free, requires 4GB+ RAM on VPS
4. Claude/Gemini — paid APIs

## Decision

**Primary: Groq API** (`llama-3.1-8b-instant`)
- Free tier: 14,000 requests/day — sufficient for 1 video/day pipeline
- No VPS RAM cost (cloud inference)
- Low latency (<1s for 512 tokens)
- Set via: `GROQ_API_KEY` + `LLM_PROVIDER=groq`

**Fallback: Ollama** (`llama3.2:3b`)
- Triggered when `GROQ_API_KEY` is empty OR Groq returns 429
- Requires Hetzner CX32 (8GB RAM) for reliable operation
- Set via: `OLLAMA_URL=http://ollama:11434` + `LLM_PROVIDER=ollama`

## Selection logic (build_llm_adapter in orchestrator.py):
```python
if os.environ.get("GROQ_API_KEY"):
    return GroqAdapter()
if os.environ.get("OLLAMA_URL"):
    return OllamaAdapter()
raise ConfigurationError("No LLM configured")
```

## Consequences
- Default CX22 (4GB) sufficient with Groq (no local model)
- Upgrade to CX32 only if Groq free tier is exhausted
