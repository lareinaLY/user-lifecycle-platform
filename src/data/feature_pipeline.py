"""Feature engineering pipeline.

Transforms raw user behavioral logs into model-ready feature vectors.
The pipeline is organized as composable feature groups (recency,
frequency, monetary, engagement, and session-derived features) so that
groups can be added or disabled without touching downstream code.

All transforms are designed to be leakage-safe: features are computed
strictly from data observable before the prediction reference time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd


@dataclass
class FeatureConfig:
    """Configuration for the feature pipeline.

    Attributes:
        reference_date: Cutoff date; only events strictly before this date
            are used to build features (prevents label leakage).
        lookback_days: Size of the historical observation window in days.
        feature_groups: Names of feature groups to compute.
    """

    reference_date: str
    lookback_days: int = 90
    feature_groups: List[str] = field(
        default_factory=lambda: ["rfm", "engagement", "session"]
    )


class FeaturePipeline:
    """End-to-end feature builder.

    Orchestrates per-group feature computation and assembles the final
    feature matrix keyed by user. Intended usage::

        pipeline = FeaturePipeline(config)
        features = pipeline.transform(raw_events)
    """

    def __init__(self, config: FeatureConfig) -> None:
        """Initialize the pipeline.

        Args:
            config: Feature pipeline configuration.
        """
        self.config = config

    def transform(self, events: pd.DataFrame) -> pd.DataFrame:
        """Build the full feature matrix.

        Args:
            events: Raw event log with at least ``user_id`` and a
                timestamp column.

        Returns:
            One row per user with the configured feature columns.
        """
        raise NotImplementedError

    def _build_rfm(self, events: pd.DataFrame) -> pd.DataFrame:
        """Compute recency / frequency / monetary features per user."""
        raise NotImplementedError

    def _build_engagement(self, events: pd.DataFrame) -> pd.DataFrame:
        """Compute engagement-depth and breadth features per user."""
        raise NotImplementedError

    def _build_session(self, events: pd.DataFrame) -> pd.DataFrame:
        """Compute session-derived features (duration, cadence) per user."""
        raise NotImplementedError

    def feature_names(self) -> List[str]:
        """Return the ordered list of output feature column names."""
        raise NotImplementedError
