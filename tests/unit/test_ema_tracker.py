"""Unit tests for EMATracker and MultiMetricTracker (Phase 5, T-400).

Test cases:
  test_first_update_equals_value         : EMA(x₀) = x₀
  test_ema_decays_toward_new_value       : moving toward new observations
  test_alpha_controls_smoothing          : higher α = faster response
  test_reset_clears_state                : reset() → n_samples=0, value=0.0
  test_multiple_metrics_independent      : metrics don't interfere
  test_deterministic                     : same sequence → same EMA
  test_serialisation_round_trip          : to_dict / from_dict round-trip
  test_multi_metric_tracker              : MultiMetricTracker basic usage
  test_alpha_validation                  : invalid alpha raises ValueError
"""
import pytest

from ytaimbot_ml.metrics.ema_tracker import EMATracker, MultiMetricTracker


def test_first_update_equals_value() -> None:
    """First EMA update: result == input value (no prior bias)."""
    tracker = EMATracker(alpha=0.3, name="ctr")
    tracker.update(0.07)
    assert tracker.value == pytest.approx(0.07)
    assert tracker.n_samples == 1


def test_ema_decays_toward_new_value() -> None:
    """After many identical updates the EMA converges to that value."""
    tracker = EMATracker(alpha=0.3, name="retention")
    tracker.update(0.0)
    for _ in range(50):
        tracker.update(1.0)
    assert tracker.value == pytest.approx(1.0, abs=1e-4)


def test_alpha_controls_smoothing() -> None:
    """alpha=0.9 responds faster to a new value than alpha=0.1."""
    fast = EMATracker(alpha=0.9, name="fast")
    slow = EMATracker(alpha=0.1, name="slow")

    for tracker in (fast, slow):
        tracker.update(0.0)

    fast.update(1.0)
    slow.update(1.0)

    assert fast.value > slow.value


def test_reset_clears_state() -> None:
    """reset() restores tracker to zero-sample state."""
    tracker = EMATracker(alpha=0.5, name="views")
    tracker.update(100.0)
    tracker.reset()
    assert tracker.n_samples == 0
    assert tracker.value == 0.0


def test_multiple_metrics_independent() -> None:
    """Updating 'ctr' does not affect 'retention' via MultiMetricTracker."""
    mt = MultiMetricTracker(alpha=0.3, metrics=["ctr", "retention"])
    mt.update("ctr", 0.07)
    assert mt.get("ctr") == pytest.approx(0.07)
    assert mt.get("retention") == 0.0


def test_deterministic() -> None:
    """Same update sequence always produces the same EMA value."""
    values = [0.05, 0.07, 0.06, 0.09, 0.04]

    def run() -> float:
        t = EMATracker(alpha=0.3, name="ctr")
        for v in values:
            t.update(v)
        return t.value

    assert run() == pytest.approx(run())


def test_serialisation_round_trip() -> None:
    """to_dict / from_dict preserves all state."""
    tracker = EMATracker(alpha=0.3, name="ctr")
    for v in [0.05, 0.07, 0.06]:
        tracker.update(v)
    restored = EMATracker.from_dict(tracker.to_dict())
    assert restored.value == pytest.approx(tracker.value)
    assert restored.n_samples == tracker.n_samples
    assert restored.alpha == pytest.approx(tracker.alpha)
    assert restored.name == tracker.name


def test_multi_metric_tracker_serialisation() -> None:
    """MultiMetricTracker round-trip via to_dict / from_dict."""
    mt = MultiMetricTracker(alpha=0.3, metrics=["ctr", "retention"])
    mt.update("ctr", 0.08)
    mt.update("retention", 0.72)
    restored = MultiMetricTracker.from_dict(mt.to_dict())
    assert restored.get("ctr") == pytest.approx(mt.get("ctr"))
    assert restored.get("retention") == pytest.approx(mt.get("retention"))


def test_alpha_validation() -> None:
    """EMATracker raises ValueError for alpha outside (0, 1)."""
    with pytest.raises(ValueError):
        EMATracker(alpha=0.0)
    with pytest.raises(ValueError):
        EMATracker(alpha=1.0)
    with pytest.raises(ValueError):
        EMATracker(alpha=-0.1)


def test_unknown_metric_returns_zero() -> None:
    """MultiMetricTracker.get on unknown metric returns 0.0."""
    mt = MultiMetricTracker(alpha=0.3)
    assert mt.get("nonexistent") == 0.0


def test_auto_register_on_update() -> None:
    """MultiMetricTracker auto-creates a tracker for a new metric."""
    mt = MultiMetricTracker(alpha=0.3)
    mt.update("new_metric", 0.5)
    assert mt.get("new_metric") == pytest.approx(0.5)
