# Copilot Instructions — YTAIMBot

## Project Purpose

Autonomous YouTube content pipeline targeting $5k+/month. Analyzes trends, generates content plans, filters via Bayesian gate, and publishes videos. Goals: CTR ≥ 6%, 30s retention ≥ 70%, 1 video/day, 99.9% uptime.

## Build, Test & Run

```bash
# Install (with dev deps)
pip install -e ".[dev]"

# Run full test suite
pytest -q --tb=short

# Run a single test file
pytest -q tests/test_orchestrator.py

# Run a single test function
pytest -q tests/test_trend_analyzer.py::test_determinism

# Run with coverage
pytest --cov=src --cov=modules --cov-report=term-missing

# Run the pipeline directly
python -m modules.orchestrator
```

CI runs on Python 3.11 and 3.12 via `.github/workflows/ci.yml`.

## Architecture — 7-Stage Pipeline

```
TrendSourceAdapter.fetch()
  → list[TrendSignal]
  → TrendAnalyzer._featurize()        # raw_score + hash-derived feature
  → TruncatedSVD (2 components)
  → TrendAnalyzer.score_trends()      # L2 magnitude, sorted desc
  → Pipeline._plan()                  # top-5 → list[ContentPlan]
  → BayesQualityFilter.decide()       # P(bad|features) → ComplianceReport
  → PublisherAdapter.publish()        # only if decision="pass" AND dry_run=False
  → PipelineResult
```

**Fail-closed**: Publishing never executes unless the gate passes AND `YTAIMBOT_DRY_RUN=false`. The pipeline catches all exceptions and sets `result.status = "error"`.

**Key packages:**
- `src/ytaimbot_ml/` — ML algorithms, data schemas, utilities (importable library)
- `modules/` — Orchestrator + adapter interfaces + synthetic implementations
- `tests/` — Pytest suite; no real network calls; all randomness is seeded

## Key Conventions

### Adapter Pattern
All I/O goes through ABCs in `modules/adapters/base.py`: `TrendSourceAdapter`, `StorageAdapter`, `PublisherAdapter`. Concrete implementations live in `modules/adapters/synthetic.py`. Real adapters (YouTube API, cloud storage) are future additions that follow the same interfaces.

### Data Schemas
All inter-stage data are `@dataclass` instances from `src/ytaimbot_ml/schemas.py`: `TrendSignal`, `TrendRanking`, `ContentPlan`, `ComplianceReport`, `PipelineResult`.

### Determinism
Every ML component accepts `np.random.Generator` as a constructor parameter. Use `make_rng(seed)` from `src/ytaimbot_ml/utils/random.py`. Tests always specify a seed. This is a hard requirement — no randomness without a seed.

### Public API Contract
Every public function must have:
- Full docstring
- Type annotations (including return type)
- Big-O complexity notation in docstring
- At minimum one usage example in docstring

### Configuration
Environment variables only — never config files or hardcoded values:
- `YTAIMBOT_DRY_RUN` (default: `true`) — skip publishing stage
- `YTAIMBOT_SEED` (default: `42`) — ML reproducibility
- `YTAIMBOT_DATA_DIR` — persistent volume path
- `YOUTUBE_API_KEY` — blank = use synthetic source
- `STORAGE_BACKEND` — `"memory"` or future backends

Secrets go in `.env` (never committed). See `.env.example`.

### Logging
Use stdlib `logging`. Log levels: `DEBUG` for intermediate data counts, `INFO` for stage transitions, `EXCEPTION` for failures. **Never log secrets or PII.**

### Testing
- Fixtures shared via `tests/conftest.py` (seeded `rng`, `synthetic_trends`)
- No external network calls — use synthetic/in-memory adapters
- Acceptance thresholds: top-5 trend overlap ≥ 80%, Bayes precision ≥ 80%

## AI Agent Output Contract

For any substantial code change, structure responses with:
1. **Goal** — what problem is being solved
2. **Files/modules affected**
3. **Implementation** — in Markdown code blocks
4. **Big-O complexity** of new algorithms
5. **Run example** — command to exercise the change
6. **Test example** — pytest snippet
7. **Acceptance criteria** — measurable conditions for success
8. **Risks/Fixes/Metrics** — weekly log format

## Repository Layout

```
src/ytaimbot_ml/       ← ML library (algorithms, schemas, utils)
modules/               ← Pipeline orchestrator + adapters
  adapters/base.py     ← Abstract interfaces (ABCs)
  adapters/synthetic.py← In-memory/test implementations
  orchestrator.py      ← Pipeline class (7-stage coordinator)
tests/                 ← pytest suite
docs/                  ← 30+ architecture and design docs
```

Only modify `src/ytaimbot_ml/`, `modules/`, `tests/`, and `docs/`. Do not mix ML/Backend/DevOps logic without an explicit requirement.

## Docker

```bash
docker build -t ytaimbot:latest .
docker run --env-file .env ytaimbot:latest

docker-compose up -d     # Start in background (uses ./data volume)
docker-compose logs -f   # Follow logs
```

Deployment target: Hetzner CX22, Ubuntu 22.04, docker-compose with `restart: unless-stopped`.
