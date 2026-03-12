"""Phase 10 — HyperLogLog: probabilistic unique element counter.

Roadmap tasks: T-640 (Supplement I)
Depends on:   hashlib, math

Algorithm
---------
HyperLogLog (Flajolet, Fusy, Gandouet, Meunier 2007):

  Estimate distinct count with O(m) space vs O(n) for exact counting.
  m = 2^b registers (b = precision bits, default b=14 → m=16384)

  Add(item):
    h = SHA-1(item) truncated to 64 bits
    j = h >> (64 - b)           # register index (top b bits)
    w = h & ((1 << (64-b)) - 1) # remaining bits
    M[j] = max(M[j], ρ(w))     # ρ = position of leftmost 1-bit (1-indexed)
  → O(1) per add

  Count() estimate:
    Z = 1 / Σ(2^{-M[j]})
    E = α_m × m² × Z            # raw estimate
    Apply small/large range corrections
  → O(m) per count

  Accuracy: ±1.04/√m ≈ ±0.81% for b=14
  Space:    m × 6 bits = 12KB for b=14

Use case: count unique keywords seen across all videos this month.

Status: ✅ Implemented — T-640 (Phase 10, Supplement I)
"""
from __future__ import annotations

import hashlib
import logging
import math

logger = logging.getLogger(__name__)


class HyperLogLogCounter:
    """Probabilistic distinct element counter using HyperLogLog.

    Uses the HyperLogLog algorithm (Flajolet et al. 2007) to estimate
    cardinality with O(m) space where m = 2^precision registers.

    Accuracy: ±1.04/√m ≈ ±0.81% for precision=14 (m=16384 registers)
    Space:    m × 6 bits = 12KB for precision=14

    Algorithm
    ---------
    - add(item): hash → split into register index j (top b bits) +
                 remaining bits w → M[j] = max(M[j], ρ(w))  O(1)
    - count():  Z = 1/Σ(2^{-M[j]}), E = α_m × m² × Z,
                apply small/large range corrections           O(m)

    Parameters
    ----------
    precision:
        Number of bits b for register index. Registers = 2^b.
        Valid range: 4 ≤ b ≤ 16. Default 14 → 16384 registers.

    Examples
    --------
    >>> hll = HyperLogLogCounter(precision=14)
    >>> for word in ["ghibli", "asmr", "cozy", "ghibli"]:
    ...     hll.add(word)
    >>> estimate = hll.count()
    >>> 2 <= estimate <= 5  # "ghibli" counted once, ~3 unique
    True
    """

    # Alpha_m correction constants (from HLL paper, class attribute per spec)
    _ALPHA_INF = 0.7213 / (1 + 1.079)

    def __init__(self, precision: int = 14) -> None:
        """Initialise the counter.

        Parameters
        ----------
        precision:
            Number of bits b for register index. Registers = 2^b.
            Valid range: 4 ≤ b ≤ 16. Default 14 → 16384 registers.

        Raises
        ------
        ValueError
            If precision is outside [4, 16].

        Complexity: O(m) — register array allocation.

        Examples
        --------
        >>> hll = HyperLogLogCounter(precision=10)
        >>> hll.num_registers
        1024
        """
        if not (4 <= precision <= 16):
            raise ValueError(
                f"precision must be in [4, 16], got {precision!r}"
            )
        self._precision = precision
        self._m = 1 << precision  # 2^b

        # Per-register storage (max observed ρ value)
        self._registers: list[int] = [0] * self._m

        # Alpha correction per HLL paper (section 3)
        if self._m == 16:
            self._alpha = 0.673
        elif self._m == 32:
            self._alpha = 0.697
        elif self._m == 64:
            self._alpha = 0.709
        else:
            # Correct per-m formula: 0.7213 / (1 + 1.079/m) for m >= 128
            self._alpha = 0.7213 / (1.0 + 1.079 / self._m)

        logger.debug(
            "HyperLogLogCounter initialised (precision=%d, m=%d, alpha=%.6f)",
            precision,
            self._m,
            self._alpha,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def add(self, item: str) -> None:
        """Add item to the sketch.

        Hashes *item* with SHA-1 (truncated to 64 bits), splits the hash
        into a register index ``j`` (top ``b`` bits) and remaining bits
        ``w``, then updates ``M[j] = max(M[j], ρ(w))``.

        Algorithm: O(1).

        Parameters
        ----------
        item:
            String element to add.  Duplicate items are idempotent (same
            hash → same register update).

        Examples
        --------
        >>> hll = HyperLogLogCounter(precision=14)
        >>> hll.add("ghibli")
        >>> hll.count() >= 1
        True
        """
        digest = hashlib.sha1(item.encode("utf-8")).digest()
        # Take the first 8 bytes as a 64-bit unsigned integer (big-endian)
        hash_int = int.from_bytes(digest[:8], byteorder="big")

        remaining_bits = 64 - self._precision
        j = hash_int >> remaining_bits  # top b bits → register index
        w = hash_int & ((1 << remaining_bits) - 1)  # remaining bits

        # ρ(w): position of leftmost 1-bit in a remaining_bits-wide field
        # Using Python's bit_length():  leading_zeros = remaining_bits - w.bit_length()
        # ρ = leading_zeros + 1  (position is 1-indexed from MSB)
        if w == 0:
            rho = remaining_bits + 1
        else:
            rho = remaining_bits - w.bit_length() + 1

        if rho > self._registers[j]:
            self._registers[j] = rho

    def count(self) -> int:
        """Estimate distinct element count.

        Applies the raw HyperLogLog estimator then corrects for small-range
        bias (linear counting) and large-range overflow per the original
        paper.

        Algorithm: O(m).

        Returns
        -------
        int
            Estimated number of distinct elements added since construction
            (or last implicit reset via :meth:`merge`).

        Examples
        --------
        >>> hll = HyperLogLogCounter(precision=14)
        >>> hll.count()
        0
        """
        m = self._m

        # Harmonic mean denominator: Σ 2^{-M[j]}
        z = sum(2.0 ** (-r) for r in self._registers)
        e = self._alpha * m * m / z  # raw estimate

        # Small-range correction (linear counting)
        if e <= 2.5 * m:
            v = self._registers.count(0)
            if v > 0:
                e = m * math.log(m / v)
        # Large-range correction (2^32 overflow)
        elif e > (1.0 / 30.0) * (1 << 32):
            e = -(1 << 32) * math.log(1.0 - e / (1 << 32))

        return int(round(e))

    def merge(self, other: HyperLogLogCounter) -> HyperLogLogCounter:
        """Return a new counter representing the union of two sketches.

        Both counters must share the same ``precision``.  Neither original
        is modified (immutable merge).

        Algorithm: O(m).

        Parameters
        ----------
        other:
            Another :class:`HyperLogLogCounter` with the same precision.

        Returns
        -------
        HyperLogLogCounter
            New counter whose registers are element-wise maxima.

        Raises
        ------
        ValueError
            If precisions differ.

        Examples
        --------
        >>> a = HyperLogLogCounter(precision=10)
        >>> b = HyperLogLogCounter(precision=10)
        >>> a.add("foo"); b.add("bar")
        >>> merged = a.merge(b)
        >>> merged.count() >= 1
        True
        """
        if self._precision != other._precision:
            raise ValueError(
                f"Cannot merge HLL counters with different precision: "
                f"{self._precision} vs {other._precision}"
            )
        merged = HyperLogLogCounter(precision=self._precision)
        merged._registers = [
            max(a, b) for a, b in zip(self._registers, other._registers)
        ]
        return merged

    def __len__(self) -> int:
        """Alias for :meth:`count`. O(m).

        Examples
        --------
        >>> hll = HyperLogLogCounter(precision=14)
        >>> len(hll)
        0
        """
        return self.count()

    @property
    def precision(self) -> int:
        """Number of precision bits b. O(1).

        Examples
        --------
        >>> HyperLogLogCounter(precision=12).precision
        12
        """
        return self._precision

    @property
    def num_registers(self) -> int:
        """Number of registers m = 2^precision. O(1).

        Examples
        --------
        >>> HyperLogLogCounter(precision=10).num_registers
        1024
        """
        return self._m


# ---------------------------------------------------------------------------
# HyperLogLog — spec-compatible alias with estimate()/count property API
# ---------------------------------------------------------------------------


class HyperLogLog:
    """Probabilistic unique count estimator using HyperLogLog algorithm.

    Uses SHA-256 to hash items to 64-bit values.
    Precision parameter p controls accuracy/space tradeoff:

    - p=14: 16384 registers, ±0.81% accuracy, ~16 KB
    - p=10: 1024 registers, ±3.25% accuracy, ~1 KB

    Algorithm: HyperLogLog (2007 Flajolet-Martin variant)
    - add: O(1), estimate: O(m) where m = 2^p registers

    Examples
    --------
    >>> hll = HyperLogLog(precision=14)
    >>> for kw in ["ghibli", "asmr", "relaxing", "ghibli"]:  # ghibli duplicate
    ...     hll.add(kw)
    >>> 2 <= hll.estimate() <= 5  # estimates ~3 uniques
    True
    >>> hll.count  # exact add() call counter
    4
    """

    # Bias correction constants (standard HyperLogLog, Flajolet et al. 2007)
    _ALPHA = {16: 0.673, 32: 0.697, 64: 0.709}
    _ALPHA_DEFAULT = 0.7213 / (1.0 + 1.079 / 2**14)  # for m >= 128

    def __init__(self, precision: int = 14) -> None:
        """Initialise the sketch.

        Parameters
        ----------
        precision : int
            Number of bits for register index (4 <= p <= 16). m = 2^p registers.

        Raises
        ------
        ValueError
            If precision is outside [4, 16].

        Complexity: O(m) — register array allocation.

        Examples
        --------
        >>> hll = HyperLogLog(precision=10)
        >>> hll.precision
        10
        """
        if not 4 <= precision <= 16:
            raise ValueError(f"precision must be 4..16, got {precision}")
        self._p = precision
        self._m = 1 << precision  # 2^p registers
        self._registers = bytearray(self._m)  # max leading-zeros per bucket
        self._alpha = self._ALPHA.get(self._m, 0.7213 / (1.0 + 1.079 / self._m))
        self._count = 0  # raw add() call counter

        logger.debug(
            "HyperLogLog initialised (precision=%d, m=%d, alpha=%.6f)",
            precision,
            self._m,
            self._alpha,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def add(self, item: str) -> None:
        """Hash item and update the appropriate register. O(1).

        Hashes *item* with SHA-256 (first 64 bits), splits the hash into
        a register index ``j`` (top ``p`` bits) and remaining bits ``w``,
        then updates ``M[j] = max(M[j], ρ(w))``.

        Parameters
        ----------
        item : str
            String element to add. Duplicates produce idempotent register updates.

        Examples
        --------
        >>> hll = HyperLogLog(precision=14)
        >>> hll.add("ghibli")
        >>> hll.estimate() >= 1
        True
        """
        # SHA-256 first 16 hex chars = 64 bits
        h = int(hashlib.sha256(item.encode()).hexdigest()[:16], 16)
        remaining = 64 - self._p
        idx = h >> remaining  # top p bits → register index
        w = h & ((1 << remaining) - 1)  # remaining bits
        rho = self._leading_zeros(w, remaining) + 1  # position of leftmost 1-bit
        if rho > self._registers[idx]:
            self._registers[idx] = rho
        self._count += 1

    def estimate(self) -> int:
        """Estimate cardinality using HyperLogLog formula. O(m).

        Applies small-range (LinearCounting) and large-range corrections
        per Flajolet et al. 2007.

        Returns
        -------
        int
            Estimated number of distinct elements.

        Examples
        --------
        >>> hll = HyperLogLog(precision=14)
        >>> hll.estimate()
        0
        """
        m = self._m
        raw = self._alpha * m * m / sum(2.0 ** -r for r in self._registers)

        # Small-range correction: LinearCounting
        zeros = self._registers.count(0)
        if raw <= 2.5 * m and zeros > 0:
            return round(m * math.log(m / zeros))

        # Large-range correction (2^32 limit)
        if raw <= (1 << 32) / 30:
            return round(raw)
        return round(-(1 << 32) * math.log(1.0 - raw / (1 << 32)))

    def merge(self, other: "HyperLogLog") -> "HyperLogLog":
        """Merge two HyperLogLog sketches (union operation). O(m).

        Returns a new HyperLogLog whose registers are the element-wise
        maxima of *self* and *other*. Neither original is modified.
        Both must have the same precision.

        Parameters
        ----------
        other : HyperLogLog
            Sketch with identical precision.

        Returns
        -------
        HyperLogLog
            New merged sketch.

        Raises
        ------
        ValueError
            If precisions differ.

        Examples
        --------
        >>> a = HyperLogLog(precision=10)
        >>> b = HyperLogLog(precision=10)
        >>> a.add("foo"); b.add("bar")
        >>> merged = a.merge(b)
        >>> merged.estimate() >= 1
        True
        """
        if self._p != other._p:
            raise ValueError(
                f"Cannot merge HyperLogLog with different precision: "
                f"{self._p} vs {other._p}"
            )
        merged = HyperLogLog(self._p)
        for i in range(self._m):
            merged._registers[i] = max(self._registers[i], other._registers[i])
        merged._count = self._count + other._count
        return merged

    @property
    def count(self) -> int:
        """Total number of items added (not unique count). O(1).

        Examples
        --------
        >>> hll = HyperLogLog()
        >>> hll.add("a"); hll.add("a")
        >>> hll.count
        2
        """
        return self._count

    @property
    def precision(self) -> int:
        """Precision parameter p. O(1).

        Examples
        --------
        >>> HyperLogLog(precision=12).precision
        12
        """
        return self._p

    @staticmethod
    def _leading_zeros(val: int, bits: int) -> int:
        """Count leading zeros in *val* within a *bits*-wide window. O(bits).

        Parameters
        ----------
        val : int
            Non-negative integer to inspect.
        bits : int
            Bit-width of the field.

        Returns
        -------
        int
            Number of leading zero bits (0 … bits).

        Examples
        --------
        >>> HyperLogLog._leading_zeros(0, 8)
        8
        >>> HyperLogLog._leading_zeros(0b10000000, 8)
        0
        >>> HyperLogLog._leading_zeros(0b00010000, 8)
        3
        """
        if val == 0:
            return bits
        count = 0
        for shift in range(bits - 1, -1, -1):
            if val >> shift & 1:
                break
            count += 1
        return count

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"HyperLogLog(precision={self._p}, estimate={self.estimate()}, "
            f"count={self._count})"
        )
