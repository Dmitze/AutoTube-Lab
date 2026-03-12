"""Unit tests for HyperLogLogCounter."""
from __future__ import annotations

import pytest

from ytaimbot_ml.utils.hyperloglog import HyperLogLogCounter


# ---------------------------------------------------------------------------
# Construction / basic properties
# ---------------------------------------------------------------------------


def test_precision_affects_registers():
    hll8 = HyperLogLogCounter(precision=8)
    hll12 = HyperLogLogCounter(precision=12)
    assert hll8.num_registers == 256
    assert hll12.num_registers == 4096
    assert hll8.precision == 8
    assert hll12.precision == 12


def test_different_precision_levels():
    for b in [4, 8, 10, 14, 16]:
        hll = HyperLogLogCounter(precision=b)
        assert hll.num_registers == 2**b
        assert hll.precision == b


# ---------------------------------------------------------------------------
# Empty counter
# ---------------------------------------------------------------------------


def test_empty_count_zero():
    hll = HyperLogLogCounter(precision=14)
    assert hll.count() == 0


def test_len_alias():
    hll = HyperLogLogCounter(precision=14)
    assert len(hll) == hll.count() == 0


# ---------------------------------------------------------------------------
# Single / duplicate elements
# ---------------------------------------------------------------------------


def test_single_element():
    hll = HyperLogLogCounter(precision=14)
    hll.add("ghibli")
    # With small-range correction the estimate should be very close to 1
    assert 1 <= hll.count() <= 3


def test_duplicate_items_counted_once():
    hll = HyperLogLogCounter(precision=14)
    for _ in range(100):
        hll.add("ghibli")
    # Only 1 unique item — small-range correction should give ≈1
    assert hll.count() <= 5


def test_add_empty_string():
    """Empty string must be hashable and not raise."""
    hll = HyperLogLogCounter(precision=14)
    hll.add("")
    assert hll.count() >= 1


# ---------------------------------------------------------------------------
# Accuracy
# ---------------------------------------------------------------------------


def test_count_estimate_accuracy():
    """1 000 unique items → estimate within 10 % of 1 000."""
    hll = HyperLogLogCounter(precision=14)
    n = 1_000
    for i in range(n):
        hll.add(f"item_{i}")
    estimate = hll.count()
    assert 900 <= estimate <= 1_100, f"Expected ~1000, got {estimate}"


def test_large_cardinality():
    """10 000 unique items → estimate within 15 % of 10 000."""
    hll = HyperLogLogCounter(precision=14)
    n = 10_000
    for i in range(n):
        hll.add(f"unique_{i}")
    estimate = hll.count()
    assert 8_500 <= estimate <= 11_500, f"Expected ~10000, got {estimate}"


def test_deterministic_same_seed():
    """Same items added in the same order must always produce the same count."""
    items = [f"word_{i}" for i in range(500)]

    hll1 = HyperLogLogCounter(precision=14)
    hll2 = HyperLogLogCounter(precision=14)
    for item in items:
        hll1.add(item)
        hll2.add(item)

    assert hll1.count() == hll2.count()


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


def test_merge_union():
    """Merge of two disjoint sketches should contain elements from both."""
    a = HyperLogLogCounter(precision=12)
    b = HyperLogLogCounter(precision=12)

    for i in range(500):
        a.add(f"setA_{i}")
    for i in range(500):
        b.add(f"setB_{i}")

    merged = a.merge(b)
    estimate = merged.count()
    # 1000 unique total → expect within 20 % for precision=12
    assert 800 <= estimate <= 1_200, f"Expected ~1000, got {estimate}"


def test_merge_does_not_modify_originals():
    a = HyperLogLogCounter(precision=10)
    b = HyperLogLogCounter(precision=10)
    a.add("alpha")
    b.add("beta")

    count_a_before = a.count()
    count_b_before = b.count()

    _ = a.merge(b)

    assert a.count() == count_a_before
    assert b.count() == count_b_before


def test_merge_different_precision_raises():
    a = HyperLogLogCounter(precision=8)
    b = HyperLogLogCounter(precision=10)
    with pytest.raises(ValueError, match="precision"):
        a.merge(b)


# ===========================================================================
# HyperLogLog (SHA-256 / estimate() / count property API)
# ===========================================================================

from ytaimbot_ml.utils.hyperloglog import HyperLogLog  # noqa: E402


def test_hyperloglog_empty_estimate_zero() -> None:
    """Empty sketch reports 0 distinct elements."""
    hll = HyperLogLog(precision=14)
    assert hll.estimate() == 0


def test_hyperloglog_single_item() -> None:
    """After adding one item the estimate is at least 1."""
    hll = HyperLogLog(precision=14)
    hll.add("ghibli")
    assert hll.estimate() >= 1


def test_hyperloglog_duplicates_not_counted() -> None:
    """Duplicate items do not inflate the estimate significantly."""
    hll = HyperLogLog(precision=14)
    for _ in range(100):
        hll.add("repeated")
    assert 1 <= hll.estimate() <= 5


def test_hyperloglog_accuracy_100_items() -> None:
    """Adding 100 unique items yields estimate within ±15."""
    hll = HyperLogLog(precision=14)
    for i in range(100):
        hll.add(f"keyword_{i}")
    estimate = hll.estimate()
    assert abs(estimate - 100) <= 15, f"estimate={estimate} too far from 100"


def test_hyperloglog_count_all_adds() -> None:
    """count property equals total add() calls, including duplicates."""
    hll = HyperLogLog(precision=14)
    items = ["a", "b", "a", "c", "b", "d"]
    for item in items:
        hll.add(item)
    assert hll.count == len(items)


def test_hyperloglog_precision_4() -> None:
    """precision=4 (minimum) creates 16 registers and works."""
    hll = HyperLogLog(precision=4)
    assert hll.precision == 4
    hll.add("test")
    assert hll.estimate() >= 1


def test_hyperloglog_precision_16() -> None:
    """precision=16 (maximum) creates 65536 registers and works."""
    hll = HyperLogLog(precision=16)
    assert hll.precision == 16
    hll.add("test")
    assert hll.estimate() >= 1


def test_hyperloglog_invalid_precision_raises() -> None:
    """precision outside [4, 16] raises ValueError."""
    with pytest.raises(ValueError):
        HyperLogLog(precision=3)
    with pytest.raises(ValueError):
        HyperLogLog(precision=17)
    with pytest.raises(ValueError):
        HyperLogLog(precision=0)


def test_hyperloglog_merge_same_precision() -> None:
    """Merging two sketches of same precision returns union estimate."""
    a = HyperLogLog(precision=10)
    b = HyperLogLog(precision=10)
    a.add("foo")
    b.add("bar")
    merged = a.merge(b)
    assert merged.estimate() >= 1
    assert a.count == 1
    assert b.count == 1
    assert merged.count == 2


def test_hyperloglog_merge_different_precision_raises() -> None:
    """Merging sketches with different precisions raises ValueError."""
    a = HyperLogLog(precision=10)
    b = HyperLogLog(precision=12)
    with pytest.raises(ValueError):
        a.merge(b)


def test_hyperloglog_leading_zeros_static() -> None:
    """_leading_zeros counts leading zeros in a fixed-width integer."""
    assert HyperLogLog._leading_zeros(0, 8) == 8
    assert HyperLogLog._leading_zeros(0b10000000, 8) == 0
    assert HyperLogLog._leading_zeros(0b00010000, 8) == 3
    assert HyperLogLog._leading_zeros(0b01000000, 8) == 1
    assert HyperLogLog._leading_zeros(0b0101, 4) == 1
    assert HyperLogLog._leading_zeros(0, 4) == 4


def test_hyperloglog_add_returns_none() -> None:
    """add() returns None (no explicit return value)."""
    hll = HyperLogLog(precision=14)
    result = hll.add("test")
    assert result is None
