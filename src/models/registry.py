"""Model version management.

Defines an MLflow-compatible registry abstraction plus a local
filesystem implementation. Training and serving code depend only on the
abstract ``ModelRegistry`` interface, so the backing store can be swapped
from the local implementation to a managed MLflow tracking server in
production without changing upstream code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ModelRegistry(ABC):
    """Abstract model registry aligned with MLflow API.

    Local implementation for development; swappable to MLflow
    in production without changing upstream code.
    """

    @abstractmethod
    def log_params(self, params: Dict[str, Any]) -> None:
        """Record the hyperparameters of the current run.

        Args:
            params: Mapping of parameter name to value.
        """
        ...

    @abstractmethod
    def log_metrics(self, metrics: Dict[str, float]) -> None:
        """Record evaluation metrics of the current run.

        Args:
            metrics: Mapping of metric name to value (e.g. ``auc``, ``logloss``).
        """
        ...

    @abstractmethod
    def save_model(self, model: Any, name: str) -> str:
        """Persist a model artifact and register a new version.

        Args:
            model: The fitted model object to persist.
            name: Registered model name.

        Returns:
            The version identifier assigned to the saved model.
        """
        ...

    @abstractmethod
    def load_model(self, name: str, version: str) -> Any:
        """Load a previously registered model.

        Args:
            name: Registered model name.
            version: Version identifier to load.

        Returns:
            The deserialized model object.
        """
        ...


class LocalModelRegistry(ModelRegistry):
    """File-system based registry.

    Storage layout:
        models/v{seq}_{date}_{trigger}/
            ├── model.pkl
            ├── params.json
            ├── metrics.json
            ├── features.json
            └── metadata.json
    """

    def __init__(self, root: str = "models") -> None:
        """Initialize the registry.

        Args:
            root: Root directory under which model versions are stored.
                This directory is git-ignored.
        """
        self.root = root
        self._pending_params: Dict[str, Any] = {}
        self._pending_metrics: Dict[str, float] = {}

    def log_params(self, params: Dict[str, Any]) -> None:
        raise NotImplementedError

    def log_metrics(self, metrics: Dict[str, float]) -> None:
        raise NotImplementedError

    def save_model(self, model: Any, name: str) -> str:
        raise NotImplementedError

    def load_model(self, name: str, version: str) -> Any:
        raise NotImplementedError

    def _next_version(self, name: str) -> str:
        """Compute the next sequential version directory name."""
        raise NotImplementedError

    def list_versions(self, name: str) -> list:
        """List available versions for a registered model.

        Args:
            name: Registered model name.

        Returns:
            Version identifiers, newest last.
        """
        raise NotImplementedError
