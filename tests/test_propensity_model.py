"""Tests for the propensity model and baseline."""

from __future__ import annotations

import pytest

from src.models.baseline import LogisticBaseline
from src.models.propensity_model import PropensityModel, PropensityModelConfig


def test_model_constructs_with_defaults() -> None:
    """PropensityModel should construct with a default config."""
    model = PropensityModel()
    assert isinstance(model.config, PropensityModelConfig)


def test_baseline_constructs() -> None:
    """LogisticBaseline should construct with default hyperparameters."""
    baseline = LogisticBaseline()
    assert baseline.C == 1.0


@pytest.mark.skip(reason="implementation pending")
def test_predict_proba_in_unit_interval() -> None:
    """Predicted probabilities must lie within [0, 1]."""
    raise NotImplementedError


@pytest.mark.skip(reason="implementation pending")
def test_model_beats_baseline_auc() -> None:
    """The GBM should not underperform the baseline on held-out AUC."""
    raise NotImplementedError
