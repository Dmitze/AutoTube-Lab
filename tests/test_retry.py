"""Tests for retry decorator — T-019 to T-023."""

from __future__ import annotations

import pytest

from modules.adapters.retry import NonRetryableError, RetryableError, retry


def test_success_on_first_attempt():
    calls = []

    @retry(max_retries=3, base_delay=0.0, jitter=False)
    def ok():
        calls.append(1)
        return 42

    assert ok() == 42
    assert len(calls) == 1


def test_retries_then_succeeds():
    """Fails twice, then succeeds on 3rd call."""
    calls = []

    @retry(max_retries=3, base_delay=0.0, jitter=False)
    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise RetryableError("not ready")
        return "ok"

    result = flaky()
    assert result == "ok"
    assert len(calls) == 3


def test_exhausted_retries_raises():
    @retry(max_retries=2, base_delay=0.0, jitter=False)
    def always_fails():
        raise RetryableError("always")

    with pytest.raises(RetryableError, match="always"):
        always_fails()


def test_non_retryable_raised_immediately():
    """NonRetryableError must NOT be retried."""
    calls = []

    @retry(max_retries=5, base_delay=0.0, jitter=False)
    def bad_request():
        calls.append(1)
        raise NonRetryableError("bad key")

    with pytest.raises(NonRetryableError):
        bad_request()

    assert len(calls) == 1  # called exactly once, no retry


def test_delays_are_exponential(monkeypatch):
    """Verify delay sequence: ~2s, ~4s, ~8s (no jitter)."""
    slept: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))

    @retry(max_retries=3, base_delay=2.0, jitter=False)
    def always_fails():
        raise RetryableError("x")

    with pytest.raises(RetryableError):
        always_fails()

    # 3 retries → 3 sleep calls
    assert len(slept) == 3
    assert slept[0] == pytest.approx(2.0)
    assert slept[1] == pytest.approx(4.0)
    assert slept[2] == pytest.approx(8.0)


def test_max_delay_cap(monkeypatch):
    """Delay must never exceed max_delay."""
    slept: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))

    @retry(max_retries=5, base_delay=2.0, max_delay=5.0, jitter=False)
    def always_fails():
        raise RetryableError("x")

    with pytest.raises(RetryableError):
        always_fails()

    assert all(s <= 5.0 for s in slept)


def test_jitter_deterministic_with_seed(monkeypatch):
    """Jitter is reproducible when seed is set."""
    slept_a: list[float] = []
    slept_b: list[float] = []

    @retry(max_retries=2, base_delay=1.0, jitter=True, seed=42)
    def fail_a():
        raise RetryableError("x")

    @retry(max_retries=2, base_delay=1.0, jitter=True, seed=42)
    def fail_b():
        raise RetryableError("x")

    monkeypatch.setattr("time.sleep", lambda s: slept_a.append(s))
    with pytest.raises(RetryableError):
        fail_a()

    monkeypatch.setattr("time.sleep", lambda s: slept_b.append(s))
    with pytest.raises(RetryableError):
        fail_b()

    assert slept_a == slept_b
