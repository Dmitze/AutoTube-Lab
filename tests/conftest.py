"""Shared pytest fixtures for the YTAIMBot test suite."""

from __future__ import annotations

import os
import certifi
os.environ["HTTPLIB2_CA_CERTS"] = certifi.where()

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
