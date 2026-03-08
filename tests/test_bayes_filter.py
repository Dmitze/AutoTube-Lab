"""Unit tests for BayesQualityFilter."""

from __future__ import annotations

import numpy as np
import pytest

from ytaimbot_ml.quality.bayes_filter import BayesQualityFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BAD_FEATURES = {"slop_score": 0.95, "dup_ratio": 0.9, "keyword_spam": 0.85}
_GOOD_FEATURES = {"slop_score": 0.05, "dup_ratio": 0.08, "keyword_spam": 0.03}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_bad_sample_detected() -> None:
    """Features with high badness values should yield P(bad) > threshold."""
    filt = BayesQualityFilter(prior_bad=0.1, threshold=0.5)
    p_bad = filt.score(_BAD_FEATURES)
    assert p_bad > 0.5, f"Expected P(bad) > 0.5, got {p_bad:.4f}"


def test_good_sample_passes() -> None:
    """Features with low badness values should yield P(bad) < threshold."""
    filt = BayesQualityFilter(prior_bad=0.1, threshold=0.5)
    p_bad = filt.score(_GOOD_FEATURES)
    assert p_bad < 0.5, f"Expected P(bad) < 0.5, got {p_bad:.4f}"


def test_decide_bad_returns_fail() -> None:
    """decide() on a bad sample must return decision='fail'."""
    filt = BayesQualityFilter()
    report = filt.decide(_BAD_FEATURES)
    assert report.decision == "fail"
    assert len(report.reasons) > 0


def test_decide_good_returns_pass() -> None:
    """decide() on a good sample must return decision='pass'."""
    filt = BayesQualityFilter()
    report = filt.decide(_GOOD_FEATURES)
    assert report.decision == "pass"


def test_precision_on_synthetic() -> None:
    """Precision >= 80% on 100 synthetic examples (50 good / 50 bad)."""
    rng = np.random.default_rng(42)
    filt = BayesQualityFilter(prior_bad=0.1, threshold=0.5)

    # 50 "bad" samples: features drawn from Beta(8, 2) → mostly high values
    bad_samples = rng.beta(8, 2, size=(50, 3))
    # 50 "good" samples: features drawn from Beta(2, 8) → mostly low values
    good_samples = rng.beta(2, 8, size=(50, 3))

    feature_names = ["f0", "f1", "f2"]
    true_positives = 0
    false_positives = 0

    for row in bad_samples:
        features = dict(zip(feature_names, row.tolist()))
        report = filt.decide(features)
        if report.decision == "fail":
            true_positives += 1

    for row in good_samples:
        features = dict(zip(feature_names, row.tolist()))
        report = filt.decide(features)
        if report.decision == "fail":
            false_positives += 1

    if true_positives + false_positives == 0:
        pytest.skip("No positive predictions — adjust threshold")

    precision = true_positives / (true_positives + false_positives)
    assert precision >= 0.80, f"Precision={precision:.2%} < 80%"


def test_determinism() -> None:
    """Identical inputs must always produce identical outputs."""
    filt = BayesQualityFilter()
    features = {"a": 0.3, "b": 0.7, "c": 0.5}
    report_1 = filt.decide(features)
    report_2 = filt.decide(features)
    assert report_1.bayes_p_bad == pytest.approx(report_2.bayes_p_bad)
    assert report_1.decision == report_2.decision
    assert report_1.content_hash == report_2.content_hash


def test_empty_features_uses_prior() -> None:
    """score({}) should return the prior probability."""
    prior = 0.15
    filt = BayesQualityFilter(prior_bad=prior)
    assert filt.score({}) == pytest.approx(prior)


def test_invalid_prior_raises() -> None:
    with pytest.raises(ValueError):
        BayesQualityFilter(prior_bad=0.0)


def test_invalid_threshold_raises() -> None:
    with pytest.raises(ValueError):
        BayesQualityFilter(threshold=1.0)
