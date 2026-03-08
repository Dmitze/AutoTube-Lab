# AI Agent Spec (v2) — ML Implementation for “YouTube AI Money Bot 2026” (YTAIMBot)
Role: Senior AI/ML Engineer (agentic systems + content generation)  
Niche: **AI‑туторіали для розробників** (Python/JS/DevOps/LLM tools)  
Owner: Lead Developer (Python/JS)  
Primary objective: Build ML modules that make the bot **autonomous, adaptive, and profitable** with a target of **$5k+/month**.

Мотивація: **“Після запуску бот працює сам і приносить гроші.”**  
Фінальна мотивація: **“Оптимізація = швидкий пасивний дохід.”**

---

## 0) Hard Requirements (must follow)
### 0.1 Non‑functional constraints
1) **No external network calls in unit tests** (no YouTube API, no ElevenLabs, no Google Trends).
2) Tests must be **deterministic**: every algorithm supports `seed` or accepts `np.random.Generator`.
3) Every public function/class must have:
   - clear docstring,
   - input/output shapes,
   - Big‑O complexity (with assumptions).
4) "Production" code must support **dry‑run** mode and **mockable interfaces**.
5) Keep dependencies minimal and CPU‑friendly by default.

### 0.2 Required math integrations (from course)
- Linear algebra (Topic 1–2): **PCA/SVD**
- Analysis (Topic 6): **FFT** (prosody shaping)
- Probabilities/ML:
  - Topic 7: **Bayes** (quality/risk filter; alert probability)
  - Topic 8: **LDA** (topics)
  - Topic 10: **EM** (mixture model / audience clusters)
  - Topic 11: **Genetic algorithms** (voice parameter evolution)
  - Topic 12: **Gradient descent** (used in PPO training; PyTorch)
- Algorithms (Topic 9): **Monte‑Carlo** (views simulation)

### 0.3 Acceptance metrics (how we “prove it works”)
Because we initially lack real labeled data, acceptance uses **synthetic ground truth** + proxy objectives:
1) **Trend prediction test on 10 trends**:
   - Metric: **Top‑5 overlap accuracy ≥ 80%** between predicted ranking and synthetic ground truth ranking.
2) Classification/topic modeling:
   - If synthetic labeled topics: **accuracy ≥ 85%** (or NMI ≥ 0.8).
3) RL (PPO) toy env:
   - Mean reward improves by ≥ 20% after N updates, AND plot exists.
4) Bayesian quality filter:
   - Rejects “bad” synthetic samples with precision ≥ 80% (proxy test).

> Important: The constraint “loss < 0.1” is not guaranteed in RL; interpret it as:
> - supervised sub‑model test OR toy env with controlled target (document assumptions).

---

## 1) System Context (agentic pipeline)
YTAIMBot is an agent system (LangChain or similar orchestration) with the cycle:

1) **Analyze**  
   - Fetch trend signals (Google Trends / YouTube search), build feature vectors  
   - Reduce dimensionality with PCA/SVD  
   - Cluster topics (LDA/EM)  
   - Score and select candidates

2) **Generate**  
   - Build script outline  
   - Generate voice with ElevenLabs (external) but locally shape prosody features  
   - Video assembly (not ML here)

3) **Optimize**  
   - SEO optimization (title/keywords/description)  
   - RL learner adjusts parameters/templates based on metrics

4) **Adapt**  
   - Update policies/config via safe rollout  
   - Continuous evaluation + drift checks

---

## 2) Repository layout (must create)
Use a real Python package to avoid “random scripts”:

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

tests/
  test_trend_analyzer.py
  test_topic_modeling.py
  test_content_generator.py
  test_learner.py
  test_bayes_filter.py

---

## 3) Data Schemas (define first; everything depends on this)
### 3.1 Trend representation
A trend is a structured object (not just strings):

- `trend_id: str`
- `keyword: str`
- `source: str` (google_trends | youtube_search)
- `region: str`
- `time_window_days: int`
- `series: list[float]` (normalized interest/time)
- `momentum: float` (slope)
- `acceleration: float` (2nd derivative proxy)
- `yt_competition: float` (proxy; e.g., result count normalized)
- `embedding: np.ndarray (d,)` optional (keyword embedding)

### 3.2 YouTube metrics schema (for learning loop)
Store per video in a normalized dict:

{
  "video_id": "string",
  "published_at": "ISO8601",
  "views_24h": 0,
  "views_7d": 0,
  "ctr": 0.0,
  "avg_view_duration_sec": 0.0,
  "retention_30s": 0.0,
  "likes": 0,
  "comments": 0,
  "rpm_estimate": 0.0,
  "cost_usd": 0.0,
  "compliance_flags": 0,
  "algorithm_version": "seo:v3",
  "policy_version": "ppo:v1"
}

---

## 4) Module Specs (step‑by‑step)

# Step 1 — `trend_analyzer.py` (PCA/SVD + Monte‑Carlo)
### Goal
Turn raw trend feature matrix into:
- PCA embedding `Z`
- scores
- Monte‑Carlo view estimates
- ranked list of trends with risk

### Inputs
- `X: np.ndarray` shape `(n_trends, n_features)`
- optional `momentum: np.ndarray` shape `(n_trends,)`
- hyperparams: `k_components`, `n_trials`, `volatility`, `threshold`

### Outputs
- PCA model (mean, components, explained variance)
- `Z`
- `scores`
- per-trend Monte‑Carlo summary:
  - expected views, p10/p50/p90, prob below threshold
- `rank_idx` by expected views desc

### Required math
- PCA via SVD (Topic 1–2)
- Monte‑Carlo simulation (Topic 9)

### Complexity requirements
- PCA/SVD complexity must be stated with assumptions:
  - precise: `O(min(n,d) * n * d)`
  - simplified per course request: mention when/why it can be approximated as `O(n^2)` for covariance-based PCA or truncated methods, and clarify tradeoffs.
- Monte‑Carlo: `O(n_trials)` per trend

### Tests
- synthetic 10-trend dataset with known “popularity” latent variable
- evaluate top‑5 overlap accuracy ≥ 80%

---

# Step 2 — `content_generator.py` (FFT prosody + Genetic optimization)
### Goal
Provide local audio/prosody optimization primitives:
- FFT analysis
- band gain shaping
- GA search to tune voice parameters (not raw waveform generation)

### Required math
- FFT (Topic 6) with SciPy or NumPy
- Genetic algorithm (Topic 11)

### Complexity
- FFT: `O(T log T)`
- GA: `O(population * generations * eval_cost)`

### Tests
- FFT sanity: energy changes when applying band gains
- GA deterministic: with fixed seed returns same best params; improvement in fitness over generations

---

# Step 3 — `learner.py` (PPO, PyTorch, Topic 12)
### Goal
Policy optimization for selecting templates/params based on state (trend + history).

Reward = views, shaped:
- `reward = views - λ*cost - μ*compliance_risk`

### Requirements
- minimal PPO (policy/value nets, clipped objective)
- matplotlib RL curves

### Tests
- toy env (no external services), reward improves ≥ 20%

---

# Step 4 — `topic_modeling.py` (LDA + EM, Topic 8–10)
### Goal
Cluster trends into topics + infer audience clusters.
Implementation: sklearn LDA or EM mixture over embeddings (diag cov for speed).

### Tests
- synthetic labeled clusters, accuracy ≥ 85% (or NMI ≥ 0.8)

---

# Step 5 — `bayes_filter.py` (Topic 7)
### Goal
Posterior probability of “bad content” given signals; decision gate.

---

## 5) DoD
- `pytest -q` passes
- demos run for each module
- docstrings + Big‑O everywhere
- deterministic tests, no external calls
