"""Random-number-generator helpers."""

from __future__ import annotations

import numpy as np


def make_rng(seed: int | None = None) -> np.random.Generator:
    """Return a seeded NumPy random Generator.

    Parameters
    ----------
    seed:
        Integer seed for full reproducibility, or ``None`` for a
        non-deterministic generator.

    Returns
    -------
    np.random.Generator
    """
    return np.random.default_rng(seed)
