"""LightGBM subscription propensity model.

Primary model predicting a user's probability of converting to a paid
subscription within the prediction horizon. Includes SHAP-based
interpretability so that individual scores can be explained at the
feature level, which is required for stakeholder trust and for driving
targeted lifecycle interventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class PropensityModelConfig:
    """Hyperparameters and training configuration.

    Attributes:
        params: LightGBM parameters (objective, learning_rate, num_leaves, ...).
        num_boost_round: Maximum number of boosting iterations.
        early_stopping_rounds: Stop if validation metric does not improve
            for this many rounds.
    """

    params: Dict[str, Any] = field(default_factory=dict)
    num_boost_round: int = 1000
    early_stopping_rounds: int = 50


class PropensityModel:
    """Gradient-boosted subscription propensity model.

    Exposes ``fit`` / ``predict_proba`` plus SHAP-based explanation so the
    same object can be used in training, batch scoring, and the online
    scoring service.
    """

    def __init__(self, config: Optional[PropensityModelConfig] = None) -> None:
        """Initialize the model.

        Args:
            config: Model configuration; uses defaults when ``None``.
        """
        self.config = config or PropensityModelConfig()
        self._booster = None
        self._feature_names: List[str] = []

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[tuple] = None,
    ) -> "PropensityModel":
        """Train the model.

        Args:
            X: Training feature matrix.
            y: Binary target (1 = converted to subscription).
            eval_set: Optional ``(X_val, y_val)`` tuple for early stopping.

        Returns:
            The fitted model (``self``).
        """
        raise NotImplementedError

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict subscription probability.

        Args:
            X: Feature matrix.

        Returns:
            Array of positive-class probabilities, shape ``(n_samples,)``.
        """
        raise NotImplementedError

    def explain(self, X: pd.DataFrame) -> np.ndarray:
        """Compute SHAP values for the given samples.

        Args:
            X: Feature matrix.

        Returns:
            SHAP value matrix aligned to ``X`` columns.
        """
        raise NotImplementedError

    def feature_importance(self) -> Dict[str, float]:
        """Return global feature importance scores.

        Returns:
            Mapping of feature name to importance value.
        """
        raise NotImplementedError
