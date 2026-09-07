"""Penalty probability configuration and payoff matrix generation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .models import GoalZone, PayoffMatrix


DEFAULT_PENALTY_PROBABILITIES = np.array(
    [
        [0.30, 0.85, 0.90, 0.80, 0.85, 0.90],
        [0.85, 0.35, 0.85, 0.90, 0.80, 0.90],
        [0.90, 0.85, 0.30, 0.80, 0.85, 0.90],
        [0.75, 0.85, 0.80, 0.30, 0.85, 0.80],
        [0.85, 0.75, 0.85, 0.85, 0.40, 0.85],
        [0.80, 0.85, 0.75, 0.80, 0.85, 0.30],
    ],
    dtype=float,
)


@dataclass(frozen=True)
class PenaltyProbabilityModel:
    """Configurable probability model for penalty outcomes.

    The values represent P(score | shooter_zone, goalkeeper_zone).
    """

    probabilities: np.ndarray
    shooter_zones: tuple[GoalZone, ...]
    goalkeeper_zones: tuple[GoalZone, ...]

    def __post_init__(self) -> None:
        probabilities = np.asarray(self.probabilities, dtype=float)
        if probabilities.ndim != 2:
            raise ValueError("Penalty probability matrix must be two-dimensional.")
        rows, cols = probabilities.shape
        if rows != cols:
            raise ValueError("Penalty probability matrix must be square.")
        if len(self.shooter_zones) != rows or len(self.goalkeeper_zones) != cols:
            raise ValueError("Penalty zones must match matrix dimensions.")
        if np.any(probabilities < 0.0) or np.any(probabilities > 1.0):
            raise ValueError("Penalty probabilities must lie in [0, 1].")
        object.__setattr__(self, "probabilities", probabilities)


def default_penalty_probability_model() -> PenaltyProbabilityModel:
    return PenaltyProbabilityModel(
        probabilities=DEFAULT_PENALTY_PROBABILITIES.copy(),
        shooter_zones=GoalZone.ordered(),
        goalkeeper_zones=GoalZone.ordered(),
    )


def build_payoff_matrix(model: PenaltyProbabilityModel) -> PayoffMatrix:
    """Convert the probability model into the shooter payoff matrix.

    The goalkeeper payoff is the negative of this matrix, so the game is zero-sum.
    """

    shooter_labels = tuple(zone.label for zone in model.shooter_zones)
    goalkeeper_labels = tuple(zone.label for zone in model.goalkeeper_zones)
    return PayoffMatrix(
        values=model.probabilities.copy(),
        row_labels=shooter_labels,
        column_labels=goalkeeper_labels,
    )


def build_default_penalty_payoff_matrix() -> PayoffMatrix:
    return build_payoff_matrix(default_penalty_probability_model())