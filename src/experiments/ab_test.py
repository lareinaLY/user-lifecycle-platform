"""A/B testing framework.

Provides deterministic, hash-based experiment assignment and statistical
significance testing for evaluating lifecycle interventions (e.g. which
users to target based on propensity scores). Hash-based assignment makes
bucketing stateless and reproducible: the same user always lands in the
same variant for a given experiment, without storing assignments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Variant:
    """A single experiment arm.

    Attributes:
        name: Variant identifier (e.g. ``"control"``, ``"treatment"``).
        weight: Relative traffic share; weights are normalized across arms.
    """

    name: str
    weight: float = 1.0


@dataclass
class ExperimentResult:
    """Outcome of a significance test between two variants.

    Attributes:
        control_rate: Observed metric rate in the control arm.
        treatment_rate: Observed metric rate in the treatment arm.
        lift: Relative lift of treatment over control.
        p_value: Two-sided p-value of the test.
        significant: Whether ``p_value`` is below the configured alpha.
    """

    control_rate: float
    treatment_rate: float
    lift: float
    p_value: float
    significant: bool


class ABTest:
    """Deterministic A/B test with hash-based assignment.

    Example::

        test = ABTest("paywall_copy_v2", [Variant("control"), Variant("treatment")])
        arm = test.assign(user_id)
    """

    def __init__(
        self,
        name: str,
        variants: List[Variant],
        salt: Optional[str] = None,
    ) -> None:
        """Initialize the experiment.

        Args:
            name: Unique experiment name; also used as the default hash salt.
            variants: The experiment arms.
            salt: Optional explicit salt to decorrelate assignment from
                other experiments sharing the same user space.
        """
        self.name = name
        self.variants = variants
        self.salt = salt or name

    def assign(self, unit_id: str) -> str:
        """Assign a randomization unit to a variant deterministically.

        Args:
            unit_id: Stable identifier for the randomization unit (user_id).

        Returns:
            The assigned variant name.
        """
        raise NotImplementedError

    def _bucket(self, unit_id: str) -> float:
        """Map a unit id to a stable bucket in ``[0, 1)`` via hashing."""
        raise NotImplementedError

    @staticmethod
    def evaluate(
        control_conversions: int,
        control_total: int,
        treatment_conversions: int,
        treatment_total: int,
        alpha: float = 0.05,
    ) -> ExperimentResult:
        """Run a two-proportion significance test.

        Args:
            control_conversions: Successes in the control arm.
            control_total: Sample size of the control arm.
            treatment_conversions: Successes in the treatment arm.
            treatment_total: Sample size of the treatment arm.
            alpha: Significance threshold.

        Returns:
            The populated :class:`ExperimentResult`.
        """
        raise NotImplementedError
