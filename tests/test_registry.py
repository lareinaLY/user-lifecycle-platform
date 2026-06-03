"""Tests for the model registry."""

from __future__ import annotations

import pytest

from src.models.registry import LocalModelRegistry, ModelRegistry


def test_local_registry_is_a_registry() -> None:
    """LocalModelRegistry should implement the ModelRegistry interface."""
    registry = LocalModelRegistry(root="models")
    assert isinstance(registry, ModelRegistry)


def test_abstract_registry_cannot_instantiate() -> None:
    """The abstract base class must not be directly instantiable."""
    with pytest.raises(TypeError):
        ModelRegistry()  # type: ignore[abstract]


@pytest.mark.skip(reason="implementation pending")
def test_save_then_load_roundtrip(tmp_path) -> None:
    """A saved model should load back as an equivalent object."""
    raise NotImplementedError


@pytest.mark.skip(reason="implementation pending")
def test_versions_increment(tmp_path) -> None:
    """Saving the same model name twice should yield distinct versions."""
    raise NotImplementedError
