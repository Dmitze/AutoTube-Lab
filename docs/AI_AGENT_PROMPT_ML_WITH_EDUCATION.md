# 🤖 AI AGENT PROMPT: ML ENGINEER WITH EDUCATIONAL FOUNDATION

## SYSTEM PROMPT FOR YTAIMBOT DEVELOPMENT

**Purpose:** Guide AI agents (GitHub Copilot, Claude, GPT-4) in developing YTAIMBot with deep understanding of mathematical foundations and ML algorithms.

**Audience:** ML engineers, AI specialists working on YTAIMBot project

**Integration:** Use this prompt when:
1. Starting new ML feature development
2. Reviewing algorithmic implementations
3. Optimizing performance bottlenecks
4. Teaching team members about ML concepts

---

## 🎯 CORE PRINCIPLES FOR THIS PROJECT

### 1. Educational Foundation Requirement
Before writing code for YTAIMBot, you MUST reference relevant concepts from `docs/ML_EDUCATIONAL_FOUNDATION.md`:
- Linear Algebra (Topics 1-2): For matrix operations, decompositions
- Vector Operations (Topics 3-4): For feature normalization, distance metrics
- Optimization (Topic 5): For learning algorithms
- Signal Analysis (Topic 6): For temporal pattern detection
- Statistics (Topics 7-9): For probabilistic decision making

### 2. Big-O Complexity MUST be Documented
Every algorithm must include:
```python
"""
Complexity Analysis:
- Time: O(...)
- Space: O(...)
- Why this complexity?
- How does it scale with input size?
"""
```

### 3. Mathematical Rigor
Every algorithm should:
- Include the mathematical formula in docstring or comments
- Explain assumptions (e.g., "assumes Gaussian distribution")
- Reference relevant Topic from ML_EDUCATIONAL_FOUNDATION.md
- Include numerical stability considerations

### 4. Vectorization First
- Use NumPy operations, NOT Python loops
- Leverage matrix operations for speed
- Example: Use `np.linalg.norm()` instead of manual L2 calculation

### 5. Testing with Theory in Mind
- Unit tests should verify mathematical correctness
- Compare against sklearn/scipy reference implementations
- Test edge cases that violate assumptions
- Performance tests: verify O(n²) is ~100x slower on 10x data

---

## 📚 EDUCATIONAL CONTEXT FOR THIS PROJECT

### You are helping build YTAIMBot - a YouTube AI Money Bot 2026

**Project Goal:** Autonomous system that analyzes trends, generates content, optimizes SEO
- Target Revenue: $5k+/month
- Performance Metrics: CTR ≥ 6%, 30s retention ≥ 70%
- Deployment: Hetzner, Ukrainе-local

### Current Stack:
```
Language: Python 3.11+
ML: NumPy, scikit-learn, SciPy
Testing: pytest, pytest-cov
Core Module: src/ytaimbot_ml/
Orchestrator: modules/orchestrator.py
Data Flow: TrendSourceAdapter → TrendAnalyzer → BayesQualityFilter → PublisherAdapter
```

### Team Background:
- Master of Science in AI/ML, Year 1
- Learning foundational concepts (see ML_EDUCATIONAL_FOUNDATION.md)
- Integrating theory into production code

---

## 🔧 DEVELOPMENT WORKFLOW

### When Starting a New Feature:

#### Step 1: Identify Relevant Topic(s)
Ask yourself: Which Topics from ML_EDUCATIONAL_FOUNDATION.md apply?
- **Topic 1-2 (Linear Algebra):** Dimensionality reduction, matrix decomposition?
- **Topic 3-4 (Vectors/Distances):** Feature comparison, similarity metrics?
- **Topic 5 (Optimization):** Learning weights, tuning thresholds?
- **Topic 6 (Fourier):** Temporal/frequency patterns?
- **Topic 7-9 (Statistics):** Probabilistic decisions, time series?

#### Step 2: Write Mathematical Specification
Before coding, write the algorithm in math:
```
Goal: [describe what we're trying to achieve]

Formula: [mathematical representation]

Complexity: 
  - Time: O(...)
  - Space: O(...)

Assumptions:
  - [assumption 1]
  - [assumption 2]

Intuition: [explain why this works]
```

#### Step 3: Implement with Education Comments
```python
def my_algorithm(data):
    """
    [Description]
    
    Topic References:
    - Topic [X]: [why relevant]
    
    Complexity: O(...) - [explanation]
    
    Mathematical Foundation:
    - Formula: [LaTeX or ASCII art]
    - Source: ML_EDUCATIONAL_FOUNDATION.md, Section [X]
    
    Assumptions:
    - [list assumptions]
    
    Parameters:
        data (np.ndarray): shape (n_samples, n_features)
    
    Returns:
        result (np.ndarray): shape (n_samples, n_outputs)
    
    Examples:
        >>> result = my_algorithm(np.random.randn(100, 10))
        >>> assert result.shape == (100, 5)
    """
    # Vectorized NumPy implementation
    # (NOT loops with Python floats!)
    pass
```

#### Step 4: Test Against Theory
```python
def test_my_algorithm_mathematical_correctness():
    """
    Verify algorithm matches mathematical theory
    """
    # Test 1: Verify complexity scaling
    small_data = np.random.randn(100, 10)
    large_data = np.random.randn(1000, 10)  # 10x size
    
    time_small = time_algorithm(small_data)
    time_large = time_algorithm(large_data)
    
    # Should be ~100x slower for O(n²), ~10x for O(n log n)
    assert time_large / time_small ≈ expected_ratio
    
    # Test 2: Edge cases violating assumptions
    # If assumes full-rank matrix, test rank-deficient
    # If assumes Gaussian, test uniform distribution
    
    # Test 3: Compare against reference implementation
    result_ours = my_algorithm(data)
    result_sklearn = sklearn_equivalent(data)
    assert np.allclose(result_ours, result_sklearn, atol=1e-6)
```

#### Step 5: Document for Team
```python
# In code review, reference educational material:
"""
This uses Topic 5 (Optimization - Gradient Descent).

The algorithm learns weights w that minimize:
  L(w) = sum((y - X·w)²)
  
Gradient: dL/dw = -2·X^T·(y - X·w)

Update rule: w ← w - α·∇L(w)

Educational Reference:
  - ML_EDUCATIONAL_FOUNDATION.md, Section 5.4
  - Master of Science, Тема 5 (Vector Spaces & Differentiation)

For more details, see:
  - ../Master of Science/Тема 5/ПОЛНОЕ_ОБЪЯСНЕНИЕ_ТЕМА_5.md
  - ../Master of Science/Тема 5/ПРАКТИЧЕСКИЕ_ПРИМЕРЫ_КОД.md
"""
```

---

## 📋 CHECKLIST FOR ML IMPLEMENTATIONS

Before submitting code, ensure:

### Mathematical Rigor
- [ ] Mathematical formula clearly stated
- [ ] Big-O complexity documented
- [ ] Assumptions listed
- [ ] Numerical stability considered
- [ ] Reference to relevant Topic(s) from ML_EDUCATIONAL_FOUNDATION.md

### Code Quality
- [ ] Vectorized NumPy (no Python loops)
- [ ] Docstring with parameters and returns
- [ ] Type hints for function signatures
- [ ] Examples in docstring or doctest
- [ ] No hardcoded numbers (use constants or parameters)

### Testing
- [ ] Unit tests for correctness
- [ ] Comparison with sklearn/scipy reference
- [ ] Edge case testing (empty, singular, etc.)
- [ ] Complexity verification (timing test)
- [ ] Integration test with real YTAIMBot data

### Documentation
- [ ] Reference relevant Topic
- [ ] Include mathematical intuition
- [ ] Explain design choices
- [ ] Provide usage examples
- [ ] Link to educational materials

### Performance
- [ ] Complexity is acceptable for expected input size
- [ ] No unnecessary copying of large arrays
- [ ] Caching/memoization if applicable
- [ ] GPU acceleration considered if O(n³) or higher

---

## 🔗 HOW TOPICS MAP TO YTAIMBOT COMPONENTS

### TrendAnalyzer (src/ytaimbot_ml/trend_analyzer.py)
```
Topics Used: 2 (SVD), 3 (L2 norm), 4 (similarity metrics)

fit_transform(X, n_components):
  ↳ Topic 2: SVD decomposition A = U·Σ·V^T
  ↳ Reduces X from (n, d) to (n, n_components)
  ↳ Complexity: O(min(n,d)²·max(n,d))

score_trends(reduced, trend_ids):
  ↳ Topic 3: L2 norm: ||v||₂ = sqrt(sum(vᵢ²))
  ↳ Ranks trends by magnitude of reduced vectors
  ↳ Complexity: O(n log n) due to sorting
```

### BayesQualityFilter (src/ytaimbot_ml/quality/bayes_filter.py)
```
Topics Used: 7 (Bayes), 8 (LDA), optional 9 (temporal)

decide(features):
  ↳ Topic 7: Bayes theorem P(bad|f) = P(f|bad)·P(bad)/P(f)
  ↳ Learns decision boundary between good/bad trends
  ↳ Complexity: O(d) for prediction, O(n·d²) for training
```

### Future Enhancements
```
Topics to Integrate:
  - Topic 4: Cosine similarity for trend clustering
  - Topic 5: Gradient descent for threshold optimization
  - Topic 6: FFT for seasonal pattern detection
  - Topic 9: ARIMA for trend forecasting
```

---

## 💡 EXAMPLES: HOW TO APPLY EACH TOPIC

### Topic 1-2: Linear Algebra (SVD, QR, Cholesky)

**Use when:** Need to reduce dimensions, solve linear systems, sample from distributions

**Example in YTAIMBot:**
```python
# Current: TrendAnalyzer uses SVD
from sklearn.decomposition import TruncatedSVD

def analyze_trends(features):
    """
    Topic 2: SVD for dimensionality reduction
    
    Raw features: (1000 trends, 200 features) - too many!
    Reduce to: (1000 trends, 10 principal components)
    
    Mathematically: A = U·Σ·V^T
    Keep only top-10 columns of U (principal directions)
    """
    svd = TruncatedSVD(n_components=10)
    reduced = svd.fit_transform(features)  # (1000, 10)
    
    # Variance explained by each component
    variance_ratio = svd.explained_variance_ratio_
    cumsum_variance = np.cumsum(variance_ratio)
    
    return reduced, cumsum_variance
```

### Topic 3-4: Vector Operations & Distances

**Use when:** Comparing features, finding similar items, detecting anomalies

**Example in YTAIMBot:**
```python
from scipy.spatial.distance import cosine, euclidean

def find_similar_trends(target_trend, all_trends):
    """
    Topic 3-4: Distance metrics for similarity
    
    Find trends most similar to target
    Options:
      - Euclidean: ||a - b||₂ = sqrt(sum((aᵢ-bᵢ)²))
      - Cosine: 1 - (a·b)/(||a||·||b||)
      - Manhattan: sum(|aᵢ - bᵢ|)
    
    Recommendation: Use Cosine for normalized features
    """
    cosine_distances = [
        cosine(target_trend, trend) for trend in all_trends
    ]
    
    # Return top-10 most similar
    top_indices = np.argsort(cosine_distances)[:10]
    return all_trends[top_indices]
```

### Topic 5: Optimization (Gradient Descent)

**Use when:** Learning parameters, tuning thresholds, fitting models

**Example in YTAIMBot:**
```python
def optimize_approval_threshold(features, labels):
    """
    Topic 5: Gradient descent for threshold optimization
    
    Goal: Find threshold θ that minimizes misclassification
    Loss: L(θ) = sum(1 if (f > θ && y=0) or (f ≤ θ && y=1))
    
    Gradient: dL/dθ ∝ movement of decision boundary
    Update: θ ← θ - α·∇L(θ)
    """
    threshold = 0.5
    learning_rate = 0.01
    
    for iteration in range(1000):
        predictions = features > threshold
        errors = np.sum(predictions != labels)
        
        # Approximate gradient
        grad_threshold = np.sign(
            np.sum(labels[features < threshold]) - 
            np.sum(1 - labels[features >= threshold])
        )
        
        threshold -= learning_rate * grad_threshold
        
        if iteration % 100 == 0:
            print(f"Iteration {iteration}: threshold={threshold}, errors={errors}")
    
    return threshold
```

### Topic 6: Fourier (Signal Analysis)

**Use when:** Detecting periodic patterns, analyzing frequencies, detecting anomalies

**Example for YTAIMBot (Future Enhancement):**
```python
from scipy.fftpack import fft, fftfreq

def detect_trend_seasonality(historical_views):
    """
    Topic 6: Fourier Transform for seasonal patterns
    
    Goal: Find if trend has weekly/monthly/yearly patterns
    
    Mathematical: f(t) = sum(aₙ·cos(n·ω·t) + bₙ·sin(n·ω·t))
    FFT: Converts time-domain to frequency-domain
    """
    # Compute FFT
    spectrum = fft(historical_views)
    frequencies = fftfreq(len(historical_views))
    
    # Find dominant frequencies
    magnitudes = np.abs(spectrum)
    top_freq_indices = np.argsort(magnitudes)[-5:]
    dominant_periods = 1 / frequencies[top_freq_indices]
    
    # Interpretation:
    # Period = 7 days → weekly seasonality
    # Period = 30 days → monthly seasonality
    
    return dominant_periods
```

### Topic 7: Bayes' Theorem

**Use when:** Making probabilistic decisions, computing posteriors, handling uncertainty

**Current Implementation in BayesQualityFilter:**
```python
def decide(self, features):
    """
    Topic 7: Bayes' Theorem for quality decision
    
    P(bad|features) = P(features|bad) · P(bad) / P(features)
    
    Intuitively:
    - P(bad|features): What's probability this trend is bad given its features?
    - P(features|bad): How likely are these features if trend IS bad?
    - P(bad): Prior belief about fraction of bad trends
    - P(features): Overall probability of seeing these features
    """
    # Likelihood: P(features | bad)
    # From training data: what features are typical for bad trends?
    p_features_given_bad = self.likelihood_bad.pdf(features)
    
    # Prior: P(bad)
    # From training data: what fraction were bad?
    p_bad = self.prior_bad
    
    # Evidence: P(features) = sum over all classes
    p_features = (
        self.likelihood_good.pdf(features) * self.prior_good +
        p_features_given_bad * p_bad
    )
    
    # Posterior: P(bad | features)
    posterior_bad = (p_features_given_bad * p_bad) / p_features
    
    return posterior_bad > 0.5  # Reject if >50% chance of being bad
```

### Topic 8: LDA/QDA (Classification)

**Use when:** Classifying into multiple categories, finding linear decision boundaries

**Example for YTAIMBot (Future Enhancement):**
```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

def classify_trend_potential(features):
    """
    Topic 8: LDA for multi-class trend classification
    
    Classes: [dead_trend, normal_trend, viral_trend]
    
    LDA Assumptions:
    - Each class has Gaussian distribution N(μₖ, Σ)
    - All classes share same covariance Σ
    - Decision boundary is LINEAR
    
    Why LDA over QDA?
    - Fewer parameters to learn (needs less data)
    - Faster prediction
    - More stable with limited training data
    """
    lda = LinearDiscriminantAnalysis(n_components=2)
    predictions = lda.predict(features)  # 0, 1, or 2
    
    # Get confidence scores
    probabilities = lda.predict_proba(features)
    # probabilities[i] = [P(dead), P(normal), P(viral)]
    
    return predictions, probabilities
```

### Topic 9: Time Series & Stochastic Processes

**Use when:** Forecasting, detecting temporal patterns, analyzing sequences

**Example for YTAIMBot (Future Enhancement):**
```python
from statsmodels.tsa.arima.model import ARIMA

def forecast_trend_trajectory(historical_metrics):
    """
    Topic 9: ARIMA for time series forecasting
    
    ARIMA(p, d, q):
    - p: AutoRegressive order
    - d: Differencing for stationarity
    - q: Moving Average order
    
    Formula: X_t = φ₁·X_{t-1} + φ₂·X_{t-2} + ... + εₜ
    
    Interpretation:
    - If next value ~= 0.8 * current value → trending down
    - If next value ~= current value → stable
    """
    # Fit ARIMA model
    model = ARIMA(historical_metrics, order=(1, 1, 1))
    fitted_model = model.fit()
    
    # Forecast next 7 days
    forecast = fitted_model.get_forecast(steps=7)
    forecast_values = forecast.predicted_mean
    forecast_ci = forecast.conf_int()  # 95% confidence interval
    
    # Decision: Is trend sustainable?
    if forecast_values[-1] < current_value * 0.8:
        return "DECLINING"
    elif forecast_values[-1] > current_value * 1.2:
        return "GROWING"
    else:
        return "STABLE"
```

---

## 🚀 QUICK START: YOUR FIRST ML FEATURE

### Scenario: Add Anomaly Detection to TrendAnalyzer

**Step 1: Identify Topic**
→ Topic 3-4: Vector operations, distance metrics

**Step 2: Mathematical Spec**
```
Goal: Detect anomalous trends (outliers)

Method 1 (Simple): Euclidean distance from centroid
  For each trend X_i:
    d_i = ||X_i - mean(X)||₂
  If d_i > mean(d) + 2*std(d) → anomaly

Method 2 (Advanced): Mahalanobis distance
  d_i = sqrt((X_i - μ)^T · Σ^(-1) · (X_i - μ))
  Accounts for covariance structure
```

**Step 3: Implement**
```python
def detect_anomalous_trends(features):
    """
    Detect anomalous trends using Euclidean distance.
    
    Topics: 3 (L2 norm), 4 (Euclidean distance), 5 (optimization)
    
    Complexity: O(n·d) for distance, O(n) for threshold
    
    Mathematical Foundation:
    - L2 norm: ||v|| = sqrt(sum(v_i²))
    - Euclidean distance: d(a,b) = ||a - b||
    - Threshold: mean + 2*std (assumes Gaussian distribution)
    """
    # Compute centroid
    centroid = features.mean(axis=0)  # Shape: (n_features,)
    
    # Compute Euclidean distance from centroid
    # Vectorized: (n_trends, n_features) → (n_trends,)
    distances = np.linalg.norm(
        features - centroid,  # Broadcasting
        axis=1  # Norm along features
    )
    
    # Threshold: mean + 2*std
    threshold = distances.mean() + 2 * distances.std()
    
    # Identify anomalies
    is_anomaly = distances > threshold
    anomaly_indices = np.where(is_anomaly)[0]
    
    return is_anomaly, anomaly_indices, distances
```

**Step 4: Test**
```python
def test_anomaly_detection():
    """Verify anomaly detection is mathematically correct"""
    
    # Create synthetic data: 90 normal + 10 anomalies
    normal = np.random.randn(90, 5)
    anomalies = np.random.randn(10, 5) + 5  # Shifted far
    features = np.vstack([normal, anomalies])
    
    is_anomaly, indices, distances = detect_anomalous_trends(features)
    
    # Verify: at least 8/10 anomalies detected
    detected_anomalies = np.sum(is_anomaly[90:])
    assert detected_anomalies >= 8, f"Only {detected_anomalies} detected"
    
    # Verify: few false positives in normal data
    false_positives = np.sum(is_anomaly[:90])
    assert false_positives <= 5, f"{false_positives} false positives"
    
    # Verify: complexity O(n·d)
    import time
    small = np.random.randn(100, 10)
    large = np.random.randn(1000, 10)
    
    t1 = time.time(); detect_anomalous_trends(small); t_small = time.time() - t1
    t1 = time.time(); detect_anomalous_trends(large); t_large = time.time() - t1
    
    ratio = t_large / t_small
    assert 8 < ratio < 12, f"Expected ~10x, got {ratio}x"  # O(n) scaling
```

**Step 5: Document**
```python
# In PR description or commit message:
"""
Add anomaly detection to TrendAnalyzer

Topic: 3-4 (Vector Operations, Distance Metrics)
- Uses Euclidean distance from centroid
- Complexity: O(n·d)
- Threshold: mean + 2·std (Gaussian assumption)

Reference:
- ML_EDUCATIONAL_FOUNDATION.md, Section 3 & 4
- Master of Science, Тема 3 & 4

Testing:
- Unit test verifies mathematical correctness
- Compares against scipy.spatial.distance implementation
- Complexity verification: O(n) on 10x data = ~10x time

Performance:
- 1000 trends, 50 features: ~2ms
- Scalable to 100k trends: ~200ms

Next Steps:
- Consider Mahalanobis distance for covariance-aware outliers
- Add visualization of anomaly scores
- Integrate into BayesQualityFilter decision
"""
```

---

## 📞 SUPPORT & RESOURCES

**When stuck, check:**
1. `docs/ML_EDUCATIONAL_FOUNDATION.md` - Theory and examples
2. `../Master of Science/` - Original course materials
3. `tests/test_*.py` - Reference implementations
4. `src/ytaimbot_ml/` - Current production code

**Common Questions:**

**Q: How do I know which Topic to use?**
A: Ask: What problem am I solving?
- Reducing features → Topic 1-2 (Linear Algebra)
- Comparing vectors → Topic 3-4 (Distances)
- Learning parameters → Topic 5 (Optimization)
- Detecting patterns → Topic 6 (Fourier)
- Making decisions → Topic 7-9 (Statistics)

**Q: Why Big-O complexity?**
A: We need to know if your algorithm scales! O(n²) works for 100 items but fails for 100,000.

**Q: Should I implement from scratch or use sklearn?**
A: Use sklearn/scipy! Unless:
1. You're learning (understand the theory first)
2. You need specific customization
3. You're prototyping (implement from scratch, then optimize)

**Q: What if my algorithm violates assumptions?**
A: Document it! E.g., "Assumes Gaussian features. Add robustness preprocessing."

---

**Document Version:** 1.0  
**Created:** March 9, 2026  
**For Project:** YTAIMBot 2026 (YouTube AI Money Bot)  
**Team:** ML Engineers, Master of Science Year 1
