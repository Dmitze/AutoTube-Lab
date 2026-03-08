# Detailed Design — ML modules (MVP-first)

## Modules (planned)
- `src/ytaimbot_ml/trend_analyzer.py`
- `src/ytaimbot_ml/simulations/monte_carlo.py`
- `src/ytaimbot_ml/quality/bayes_filter.py`

## trend_analyzer.py (MVP)
### Inputs
- `X: np.ndarray` shape `(n_samples, n_features)`
- `rng: np.random.Generator` (optional)

### Outputs
- reduced features `(n_samples, k)`
- ranking list `[(trend_id, score)]`

### Big-O (expected)
- PCA/SVD: залежить від методу; документувати припущення (n, d, k)
- Ranking: O(n log n)

## Quality gates (MVP)
- cosine similarity: O(n*d) per compare (оптимізується кешем/індексом)
- bayes filter: O(n_features)

## Determinism policy
- всі random — тільки через injected RNG
