# Architecture Overview

This document provides an overview of the system architecture.

---

## System Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                        YTAIMBot 2026                                   │
│                                                                        │
│  ┌──────────────────┐     ┌──────────────────┐     ┌───────────────┐ │
│  │  Trend Sources   │────▶│  ML Pipeline     │────▶│  Publisher    │ │
│  │  (Adapters)      │     │  (TrendAnalyzer) │     │  (Adapter)    │ │
│  └──────────────────┘     └────────┬─────────┘     └───────────────┘ │
│                                    │                        ▲         │
│                            ┌───────▼────────┐              │         │
│                            │  Quality Gate  │──────────────┘         │
│                            │  (BayesFilter) │  pass only             │
│                            └───────┬────────┘                        │
│                                    │                                  │
│                            ┌───────▼────────┐                        │
│                            │    Storage     │                        │
│                            │  (Adapter)     │                        │
│                            └────────────────┘                        │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Components

### ML Layer (`src/ytaimbot_ml/`)

| Module | Responsibility |
|--------|---------------|
| `trend_analyzer.py` | SVD/PCA dimensionality reduction and trend ranking |
| `quality/bayes_filter.py` | Naive-Bayes quality gate (P(bad\|features)) |
| `schemas.py` | Shared data classes (TrendSignal, ContentPlan, …) |
| `utils/random.py` | Seeded RNG factory for reproducibility |

### Backend Layer (`modules/`)

| Module | Responsibility |
|--------|---------------|
| `orchestrator.py` | `Pipeline` class — coordinates all stages |
| `adapters/base.py` | Abstract adapter interfaces |
| `adapters/synthetic.py` | In-memory adapters for testing and dry-run |

### Adapters

Adapters abstract all I/O boundaries:
- **TrendSourceAdapter** — fetches raw trend signals
- **StorageAdapter** — persists pipeline artefacts
- **PublisherAdapter** — uploads approved content

---

## Data Flow

See [`ARCHITECTURE_DATAFLOW.md`](ARCHITECTURE_DATAFLOW.md) for a detailed sequence diagram.

Short summary:

1. `TrendSourceAdapter.fetch()` → list of `TrendSignal`
2. `TrendAnalyzer.analyze()` → list of `TrendRanking` (SVD + L2 sort)
3. `Pipeline._plan()` → list of `ContentPlan` (top-N)
4. `BayesQualityFilter.decide()` → `ComplianceReport` per plan
5. If `decision == "pass"` **and** `dry_run == False` → `PublisherAdapter.publish()`

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| ML | NumPy, scikit-learn (TruncatedSVD), SciPy |
| Testing | pytest, pytest-cov |
| Containerisation | Docker, docker-compose |
| CI | GitHub Actions (ubuntu-latest, Python 3.11+3.12) |
| Deployment | Hetzner CX22, Ubuntu 22.04 |

---

## Deployment Architecture

```
Hetzner CX22 (Ubuntu 22.04)
└── docker compose
    └── bot (python:3.11-slim)
        ├── modules/orchestrator.py  ← entrypoint
        ├── src/ytaimbot_ml/         ← ML library
        └── data/                    ← persistent volume
```
