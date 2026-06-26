"""Decorator for retrying functions with exponential backoff and jitter."""

from __future__ import annotations

import functools
import random
import time
from typing import Callable, ParamSpec, TypeVar

from modules.adapters.errors import NonRetryableError, RetryableError

# Re-export so callers can do:
#   from modules.adapters.retry import NonRetryableError, RetryableError, retry
__all__ = ["exponential_backoff", "retry", "RetryableError", "NonRetryableError"]

_P = ParamSpec("_P")
_R = TypeVar("_R")


def exponential_backoff(
    max_retries: int,
    base_delay: float,
    jitter: bool = True,
    seed: int | None = None, # Add seed parameter
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Decorator to retry a function with exponential backoff and optional jitter.

    Parameters
    ----------
    max_retries:
        Maximum number of times to retry the function.
    base_delay:
        The base delay in seconds for the exponential backoff (e.g., 0.1, 1.0).
    jitter:
        If True, adds a random jitter to the delay to prevent thundering herd.
    seed:
        Optional integer seed for random number generation in jitter, ensuring
        deterministic delays for testing.

    Returns
    -------
    Callable
        The decorated function.
    """

    def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            if seed is not None:
                random.seed(seed) # Apply seed if provided

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RetryableError as e:
                    if attempt == max_retries:
                        raise  # Re-raise the last exception if max retries reached

                    delay = base_delay * (2**attempt)
                    if jitter:
                        delay = delay * (1 + random.random())
                    time.sleep(delay)
            # This part should ideally not be reached, as an exception is always raised
            # or a value returned. Added for type hint completeness.
            raise RuntimeError("Should not happen: exponential_backoff decorator logic error.") # noqa

        return wrapper

    return decorator


# Convenience alias used by youtube_search.py
retry = exponential_backoff