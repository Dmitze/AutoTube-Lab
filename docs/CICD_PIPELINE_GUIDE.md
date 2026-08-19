# 🔧 CI/CD Pipeline Guide — YTAIMBot

> **Version:** 1.0.0 | **Updated:** 2026-07-21 | **Phase:** P7 Epic 7.5
> **Reference tasks:** T-479, T-480, T-481, T-482, T-483, T-484, T-485, T-486, T-487, T-488, T-489, T-490

---

## Overview

YTAIMBot uses **GitHub Actions** for all CI/CD automation. The pipeline has two main workflows:

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **CI** | `.github/workflows/ci.yml` | push/PR to `main` | Lint, tests, docker build |
| **Release** | `.github/workflows/release.yml` | push tag `v*` | Build + push to GHCR |

---

## 🔁 CI Workflow (`ci.yml`)

### Jobs (in dependency order)

```
lint ──┬──▶ test (3.11)  ──▶ ci-gate ✅
       │
       ├──▶ test (3.12)  ──▶ ci-gate ✅
       │
       └──▶ docker-build ──▶ ci-gate ✅
            (after test) ──▶ mutation (non-blocking)
```

### Job Descriptions

#### 1. `lint` — Fast gate (T-479, T-480)
Runs **first**, blocks all other jobs on failure:
- **ruff check** — PEP 8, pyflakes, isort, pyupgrade
- **ruff format** — formatting consistency check
- **bandit** — security scanner (severity `-ll`, low and above)

```bash
# Run locally:
ruff check src/ modules/ tests/ --output-format=github
ruff format --check src/ modules/ tests/
bandit -r src/ modules/ -ll -q
```

#### 2. `test` — Matrix (Python 3.11 + 3.12) (T-485, T-487)
Runs on both Python versions:
- Full `pytest` suite with `--cov` coverage report
- Coverage threshold: **≥ 80%** (will be raised to 90% in P9 T-574)
- On PRs: posts a **coverage comment** with line-by-line breakdown (3.12 only)
- Uploads `coverage.xml` + `htmlcov/` as a GitHub Actions artifact

```bash
# Run locally (equivalent):
pytest -q --tb=short \
  --cov=src --cov=modules \
  --cov-report=term-missing \
  --cov-fail-under=80
```

#### 3. `docker-build` — Verify image builds (T-481, T-488)
- Builds the Docker image without pushing
- Uses BuildX layer caching via `cache-from: type=gha`
- Targets `linux/amd64` only (faster than multi-arch)
- **Target:** build completes in < 5 minutes

#### 4. `mutation` — Non-blocking mutation test (T-553, T-559)
- Runs only after tests pass
- `continue-on-error: true` — never blocks the pipeline
- Targets `src/ytaimbot_ml/quality/` (bayes_filter, similarity_gate)

#### 5. `ci-gate` — Final summary
- Aggregates lint + test + docker-build
- Is the required status check for branch protection rules

---

## 🚀 Release Workflow (`release.yml`)

### Trigger
```bash
git tag v0.1.0 && git push origin v0.1.0
```

### Flow
1. **Pre-release CI gate** — runs lint + tests (blocks on failure)
2. **Build & push to GHCR** — multi-arch (`linux/amd64` + `linux/arm64`)
3. **Create GitHub Release** — auto-generated changelog + Docker pull instructions

### Image tags generated
| Tag pattern | Example |
|-------------|---------|
| Semver version | `ghcr.io/user/ytaimbot:0.1.0` |
| Semver major.minor | `ghcr.io/user/ytaimbot:0.1` |
| SHA prefix | `ghcr.io/user/ytaimbot:sha-abc1234` |
| `latest` | `ghcr.io/user/ytaimbot:latest` |

### Pull the released image
```bash
docker pull ghcr.io/Dmitze/YTAIMBot:0.1.0

# Run on VPS
docker run --env-file .env \
  -v $(pwd)/data:/app/data \
  ghcr.io/Dmitze/YTAIMBot:0.1.0
```

---

## 🤖 Dependabot (`dependabot.yml`) — T-484

Auto-updates run **every Monday at 09:00 Kyiv time**:
- **pip** — Python package updates (max 5 PRs open)
- **github-actions** — Actions version updates (max 3 PRs open)

Exclusions:
- `numpy` — major version updates skipped (breaking API changes)

---

## 🐳 Local Docker Test (`docker-compose.test.yml`) — T-486

Run the full test suite inside an isolated Docker container:

```bash
# Build and run tests
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Clean up
docker compose -f docker-compose.test.yml down --volumes
```

Features:
- All external API keys set to dummy values (`test-key-ci`)
- `YTAIMBOT_DRY_RUN=true` — never publishes
- Source mounted as read-only (tests can't mutate code)
- Coverage XML written to named volume `/reports/`
- Resource limits: 2 vCPU, 2GB RAM (simulate Hetzner CX22)

---

## 🔒 Branch Protection (recommended setup)

In GitHub Settings → Branches → `main`:

| Required status check | Job |
|-----------------------|-----|
| `CI Gate ✅` | `ci-gate` |
| `Lint & Security` | `lint` |
| `Test (Python 3.11)` | `test (3.11)` |
| `Test (Python 3.12)` | `test (3.12)` |
| `Docker Build Check` | `docker-build` |

---

## 📊 Coverage Badge Setup (T-482)

The coverage badge in README.md uses a gist-based endpoint. To activate:

1. Create a GitHub Gist named `ytaimbot-coverage.json`
2. Add a workflow step to update it on each `main` push:
   ```yaml
   - name: Update coverage badge gist
     uses: schneegans/dynamic-badges-action@v1.7.0
     with:
       auth: ${{ secrets.GIST_SECRET }}
       gistID: <your-gist-id>
       filename: ytaimbot-coverage.json
       label: Coverage
       message: "${{ env.COVERAGE_PCT }}%"
       color: ${{ env.COVERAGE_PCT >= 90 && 'brightgreen' || 'yellow' }}
   ```
3. Set `GIST_SECRET` in repo secrets (PAT with `gist` scope)

---

## 🗂️ CI Artifacts

| Artifact | Retention | Contents |
|----------|-----------|---------|
| `coverage-report-py3.12` | 7 days | `coverage.xml`, `htmlcov/` |

Download from **Actions → workflow run → Artifacts** section.

---

## 🔗 Related Documentation

- [Deployment Guide (VPS)](DEPLOYMENT_CLOUD_VPS.md)
- [Roadmap: Phase 7](ROADMAP_AI_AGENT_TASKS.md#phase-7)
- [Dockerfile](../Dockerfile)
- [docker-compose.yml](../docker-compose.yml)
