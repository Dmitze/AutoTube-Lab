"""Shared pytest fixtures for the YTAIMBot test suite."""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.abspath('src'))
from unittest.mock import MagicMock

# Fix for HTTPLIB2_CA_CERTS test failures in environments without certs
os.environ["HTTPLIB2_CA_CERTS"] = __file__

# Mock moviepy so tests don't require it
sys.modules['moviepy'] = MagicMock()
sys.modules['moviepy.editor'] = MagicMock()

# Keep httplib2 mocks if they were helping somewhere else, but setting HTTPLIB2_CA_CERTS should be enough.
sys.modules['httplib2'] = MagicMock()
sys.modules['httplib2.certs'] = MagicMock()

import numpy as np
import pytest

from modules.adapters.synthetic import SyntheticTrendSource
from ytaimbot_ml.schemas import TrendSignal
from ytaimbot_ml.utils.random import make_rng


@pytest.fixture()
def rng() -> np.random.Generator:
    """Seeded random generator for reproducible tests."""
    return make_rng(42)


@pytest.fixture()
def synthetic_trends() -> list[TrendSignal]:
    """10 deterministic synthetic TrendSignal objects (seed=0)."""
    return SyntheticTrendSource(seed=0).fetch()


@pytest.fixture()
def sample_features_matrix(rng: np.random.Generator) -> np.ndarray:
    """20×5 feature matrix of float values in [0, 1]."""
    return rng.uniform(0.0, 1.0, size=(20, 5))
