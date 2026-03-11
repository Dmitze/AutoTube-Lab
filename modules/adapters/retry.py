"""Exponential-backoff retry decorator for all network adapters.

Algorithms
----------
Exponential Backoff with Full Jitter (T-016, T-017):
    delay(attempt) = min(base × 2^attempt + U(0, base), max_delay)

    attempt=0 → ~2 s, attempt=1 → ~4 s, attempt=2 → ~8 s, cap=30 s
    Complexity: O(max_retries) worst case

Usage
-----
    from modules.adapters.retry import retry, RetryableError

    @retry(max_retries=3, base_delay=2.0)
    def call_api() -> list:
        ...
"""

from __future__ import annotations

import functools
import logging
import random
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)

_DEFAULT_MAX_DELAY = 30.0
_DEFAULT_BASE = 2.0


class RetryableError(Exception):
    """Transient error — safe to retry (rate-limit, timeout, 5xx)."""


class NonRetryableError(Exception):
    """Permanent error — must NOT retry (400 bad request, auth failure)."""


def retry(
    max_retries: int = 3,
    base_delay: float = _DEFAULT_BASE,
    max_delay: float = _DEFAULT_MAX_DELAY,
    jitter: bool = True,
    seed: int | None = None,
) -> Callable[[F], F]:
    """Decorator: retry *func* on :exc:`RetryableError` with exponential backoff.

    Parameters
    ----------
    max_retries:
        Maximum number of retry attempts after the first failure.
    base_delay:
        Base delay in seconds used in ``base × 2^attempt`` formula.
    max_delay:
        Hard cap on computed delay in seconds.
    jitter:
        When ``True`` (default) adds ``U(0, base)`` to the delay to
        spread thundering-herd traffic.
    seed:
        RNG seed for deterministic jitter (useful in tests).

    Returns
    -------
    Callable
        Wrapped function that retries automatically.

    Complexity
    ----------
    O(max_retries) worst-case calls.

    Examples
    --------
    >>> @retry(max_retries=2, base_delay=1.0, seed=42)
    ... def flaky():
    ...     raise RetryableError("timeout")
    >>> try:
    ...     flaky()
    ... except RetryableError:
    ...     pass  # exhausted retries
    """
    rng = random.Random(seed)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except NonRetryableError:
                    raise
                except RetryableError as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        break
                    raw = base_delay * (2 ** attempt)
                    fuzz = rng.uniform(0, base_delay) if jitter else 0.0
                    delay = min(raw + fuzz, max_delay)
                    logger.warning(
                        "%s attempt %d/%d failed (%s); retrying in %.1fs",
                        func.__qualname__,
                        attempt + 1,
                        max_retries,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
            raise last_exc  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator
