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
4) “Production” code must support **dry‑run** mode and **mockable interfaces**.
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
