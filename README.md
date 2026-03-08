# YouTube AI Money Bot 2026 — Documentation Hub

## Introduction

This repository contains planning and implementation guidance for **YouTube AI Money Bot 2026**: an autonomous system that analyzes trends, generates content, optimizes SEO, adapts to performance metrics, and is designed to support a **$5k+/month** operating target.

## Start Here

For a new AI chat or Copilot session, use the consolidated onboarding guide:

- [`docs/AI_AGENT_START_PROMPT_2026.md`](docs/AI_AGENT_START_PROMPT_2026.md)

That document defines:

- the **default niche, format, and metrics** to ask for first;
- the required repository structure (`src/ytaimbot_ml/`, `modules/`, `tests/`, `docs/`);
- the response format with **ready-to-paste Markdown blocks**;
- mandatory **Big-O**, testing, and acceptance criteria requirements;
- the rule to keep **ML / Backend / DevOps** responsibilities separate;
- the need to account for **Hetzner / UA locality / local-first deployment** when discussing infrastructure.

## Existing Detailed Specs

- [`docs/AI_AGENT_ML_IMPLEMENTATION_PROMPT.md`](docs/AI_AGENT_ML_IMPLEMENTATION_PROMPT.md)
- [`docs/AI_AGENT_ML_IMPLEMENTATION_PROMPT_V2.md`](docs/AI_AGENT_ML_IMPLEMENTATION_PROMPT_V2.md)
- [`docs/SECURITY_ERROR_HANDLING_GUIDE.md`](docs/SECURITY_ERROR_HANDLING_GUIDE.md)
- [`docs/ARCHITECTURE_DIAGRAMS_VISUALS.md`](docs/ARCHITECTURE_DIAGRAMS_VISUALS.md)
- [`tests/README.md`](tests/README.md)

## Working Rules for AI Agents

1. Ask for **niche**, **content format**, and **expected metrics** first.
2. If the user does not answer, default to:
   - **Niche:** AI tutorials for developers
   - **Format:** 8-12 minute tutorial videos + Shorts
   - **Metrics:** CTR >= 6%, 30s retention >= 70%, 1 video/day, target revenue >= $5k/month
3. Keep generated work inside:
   - `src/ytaimbot_ml/`
   - `modules/`
   - `tests/`
   - `docs/`
4. Always include:
   - Markdown blocks ready for copy/paste or commit
   - Big-O explanations
   - test examples
   - run examples
   - acceptance criteria
   - weekly risks / fixes / metrics

## Example Validation Commands

```bash
pytest -q
pytest -q tests/test_trend_analyzer.py
python -m ytaimbot_ml.trend_analyzer
```

## Motivation

> With the right structure, the AI bot behaves like an expert teammate: faster delivery, safer changes, clearer acceptance, and a stronger path to stable passive income.
