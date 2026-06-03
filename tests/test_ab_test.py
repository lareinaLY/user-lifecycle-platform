"""Tests for the A/B testing framework."""

from __future__ import annotations

import pytest

from src.experiments.ab_test import ABTest, Variant


@pytest.fixture
def test_ab() -> ABTest:
    """Return a two-arm experiment for tests."""
    return ABTest("unit_test_exp", [Variant("control"), Variant("treatment")])


def test_constructs(test_ab: ABTest) -> None:
    """ABTest should construct with the provided variants."""
    assert len(test_ab.variants) == 2


@pytest.mark.skip(reason="implementation pending")
def test_assignment_is_deterministic(test_ab: ABTest) -> None:
    """The same unit id must always map to the same variant."""
    raise NotImplementedError


@pytest.mark.skip(reason="implementation pending")
def test_assignment_respects_weights() -> None:
    """Observed split should approximate configured variant weights."""
    raise NotImplementedError


@pytest.mark.skip(reason="implementation pending")
def test_evaluate_detects_significant_lift() -> None:
    """evaluate() should flag a clearly significant difference."""
    raise NotImplementedError
