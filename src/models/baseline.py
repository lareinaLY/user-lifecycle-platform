"""Logistic regression baseline for subscription propensity.

A simple, interpretable baseline used as a reference point for the
gradient-boosted model. Keeping a baseline makes it easy to quantify the
incremental value of the more complex model and to sanity-check feature
quality and the training pipeline.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


class LogisticBaseline:
    """Regularized logistic regression propensity baseline.

    Wraps scikit-learn's ``LogisticRegression`` with standardized inputs
    and exposes the same ``fit`` / ``predict_proba`` interface as the
    primary model so the two are interchangeable in evaluation harnesses.
    """

    def __init__(self, C: float = 1.0, class_weight: Optional[str] = "balanced") -> None:
        """Initialize the baseline.

        Args:
            C: Inverse of regularization strength.
            class_weight: Class weighting strategy passed to scikit-learn,
                e.g. ``"balanced"`` to offset label imbalance.
        """
        self.C = C
        self.class_weight = class_weight
        self._model = None
        self._scaler = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "LogisticBaseline":
        """Fit the baseline on training data.

        Args:
            X: Feature matrix.
            y: Binary target (1 = converted to subscription).

        Returns:
            The fitted estimator (``self``).
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
