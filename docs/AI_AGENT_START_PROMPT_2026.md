# AI Agent Start Prompt & Summary Checklist — YouTube AI Money Bot 2026

> Мотивація: **«З цією структурою AI‑бот працюватиме як експерт, прискорюючи розробку, забезпечуючи стабільність і дохід $5k+/міс.»**

## 1. Purpose

Use this document to start a new AI chat for **ML**, **Backend**, or **DevOps** tasks in the `Dmitze/YTAIMBot` repository without breaking the project structure or acceptance requirements.

The agent must stay inside the repository conventions:

- `src/ytaimbot_ml/`
- `modules/`
- `tests/`
- `docs/`

## 2. Default discovery questions

At the start of every new task, the AI agent must ask for:

1. **Ніша / niche**
2. **Формат контенту** (shorts, long-form, tutorials, explainers, faceless, etc.)
3. **Очікувані метрики** (CTR, retention, RPM, upload cadence, monthly revenue target)

If the user does not provide them, the default assumption is:

- **Niche:** `AI-туторіали для розробників`
- **Format:** `8-12 minute tutorial videos + supporting Shorts`
- **Primary metrics:** `CTR >= 6%`, `30s retention >= 70%`, `1 video/day`, `target revenue >= $5k/month`

## 3. Response contract for every generated step

Every substantial answer must contain a **complete Markdown block ready for copy/paste or commit**.

Required sections:

1. **Goal**
2. **Files / modules affected**
3. **Implementation details**
4. **Big-O complexity**
5. **Run examples**
6. **Test examples**
7. **Acceptance Criteria**
8. **Risks / fixes / metrics**

Recommended answer template:

````markdown
## Goal
- Explain the exact deliverable.

## Files
- src/ytaimbot_ml/example.py
- tests/test_example.py

## Implementation
```python
# ready-to-paste code
```

## Big-O
- Training/inference complexity with assumptions.

## Run
```bash
python -m ytaimbot_ml.example
```

## Tests
```bash
pytest -q
```

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Risks / Fixes / Metrics
- Risk:
- Fix:
- Metric:
````

## 4. Separation of responsibilities

Do not mix feature logic and operational logic in the same task unless explicitly requested.

### ML scope

Use `src/ytaimbot_ml/` for:

- trend analysis
- topic modeling
- ranking/scoring
- Bayesian filters
- learning loops
- evaluation helpers

ML outputs must include:

- deterministic behavior (`seed` or injected RNG)
- docstrings
- Big-O
- testable synthetic examples

### Backend scope

Use `modules/` for:

- orchestration
- integrations
- workflow state
- scheduling
- storage adapters
- safe service boundaries around ML modules

Backend deliverables must include:

- typed interfaces
- error handling
- retry/timeouts where relevant
- examples of calling ML modules without duplicating ML logic

### DevOps scope

Use `docs/` plus deployment/config files for:

- CI/CD
- Docker / Compose
- Hetzner deployment
- monitoring
- backups
- incident handling

DevOps deliverables must include:

- Hetzner/UA locality assumptions
- local-first deployment notes when cloud access is limited
- monitoring and rollback strategy

## 5. Repository structure to preserve

```text
src/
  ytaimbot_ml/
    __init__.py
    schemas.py
    trend_analyzer.py
    topic_modeling.py
    content_generator.py
    learner.py
    bayes_filter.py
    utils/
      random.py
      metrics.py
      plotting.py

modules/
  orchestrators/
  integrations/
  storage/
  seo/
  publishing/

tests/
  test_trend_analyzer.py
  test_topic_modeling.py
  test_content_generator.py
  test_learner.py
  test_bayes_filter.py

docs/
  architecture/
  runbooks/
  prompts/
```

If a requested change does not fit this structure, the AI agent must explain why before proposing a new path.

## 6. Engineering expectations

### Algorithms and math

The AI agent must explain algorithmic complexity with assumptions:

- PCA/SVD: `O(min(n, d) * n * d)`; explain when covariance-based shortcuts are acceptable
- FFT: `O(T log T)`
- Monte-Carlo simulation: `O(n_trials)` per entity
- LDA / EM / clustering: describe dependence on samples, dimensions, topics, and iterations
- Genetic algorithms: `O(population * generations * eval_cost)`
- Gradient methods / PPO-style updates: explain batch, rollout, and epoch dependence

### Testing

The AI agent must provide deterministic tests and runnable examples:

```bash
pytest -q
pytest -q tests/test_trend_analyzer.py
python -m ytaimbot_ml.trend_analyzer
```

Rules:

- no external network calls in unit tests
- use synthetic data when production data is unavailable
- include mockable interfaces for integrations
- document assumptions when proxy metrics are used

## 7. Acceptance Criteria baseline

The AI agent should validate work against these defaults unless the task defines stricter requirements:

- [ ] The proposal respects `src/ytaimbot_ml/`, `modules/`, `tests/`, and `docs/`
- [ ] The answer contains ready-to-use Markdown and code blocks
- [ ] Big-O is documented for the main algorithms
- [ ] Run and test examples are included
- [ ] ML, Backend, and DevOps concerns stay separated
- [ ] Deployment/CI/CD guidance accounts for Hetzner, UA locality, or local-first fallback
- [ ] Risks, fixes, and metrics are documented for the relevant week or milestone
- [ ] The change can be reviewed without hidden assumptions

## 8. Weekly documentation rule

For each implementation week or milestone, the AI agent must record:

- **Risks**
- **Fixes / mitigations**
- **Metrics**

Minimum template:

```markdown
## Week N
- Risks:
  - ...
- Fixes:
  - ...
- Metrics:
  - CTR:
  - Retention:
  - RPM:
  - Upload throughput:
  - Infra uptime:
```

## 9. New chat prompt

Copy this into a new AI chat when starting the current highest-priority task:

````markdown
You are the implementation agent for **YouTube AI Money Bot 2026**.

Before doing any work, ask for:
1. niche,
2. content format,
3. expected metrics.

If I do not answer, use defaults:
- niche: AI tutorials for developers
- format: 8-12 minute tutorials + Shorts
- metrics: CTR >= 6%, 30s retention >= 70%, 1 video/day, $5k+/month

Mandatory rules:
- preserve repository structure: `src/ytaimbot_ml/`, `modules/`, `tests/`, `docs/`
- return complete Markdown blocks ready for copy/paste or commit
- explain Big-O for the main algorithms
- include run examples and tests
- keep ML / Backend / DevOps logic separated
- for deployment, CI/CD, and cloud decisions, account for Hetzner, UA locality, and local-first fallback
- for every week or milestone, document risks, fixes, and metrics

Required output sections:
1. Goal
2. Files / modules affected
3. Implementation
4. Big-O
5. Run examples
6. Test examples
7. Acceptance Criteria
8. Risks / Fixes / Metrics
````

## 10. Related repository documents

- `/home/runner/work/YTAIMBot/YTAIMBot/docs/AI_AGENT_ML_IMPLEMENTATION_PROMPT.md`
- `/home/runner/work/YTAIMBot/YTAIMBot/docs/AI_AGENT_ML_IMPLEMENTATION_PROMPT_V2.md`
- `/home/runner/work/YTAIMBot/YTAIMBot/Промт для AI-Агента в Ролі Backend Developer.txt`
- `/home/runner/work/YTAIMBot/YTAIMBot/Промт для AI-Агента в Ролі DevOps SRE Engineer.txt`
- `/home/runner/work/YTAIMBot/YTAIMBot/tests/README.md`
