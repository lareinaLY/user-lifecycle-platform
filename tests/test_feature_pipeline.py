"""Tests for the feature engineering pipeline."""

from __future__ import annotations

import pytest

from src.data.feature_pipeline import FeatureConfig, FeaturePipeline


@pytest.fixture
def config() -> FeatureConfig:
    """Return a minimal feature config for tests."""
    return FeatureConfig(reference_date="2024-01-01", lookback_days=30)


def test_pipeline_constructs(config: FeatureConfig) -> None:
    """Pipeline should construct from a config without error."""
    pipeline = FeaturePipeline(config)
    assert pipeline.config.lookback_days == 30


@pytest.mark.skip(reason="implementation pending")
def test_transform_one_row_per_user(config: FeatureConfig) -> None:
    """transform() should return exactly one row per unique user."""
    raise NotImplementedError


@pytest.mark.skip(reason="implementation pending")
def test_no_label_leakage(config: FeatureConfig) -> None:
    """Features must only use events before the reference date."""
    raise NotImplementedError
