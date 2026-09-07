"""Core dataclasses and enums for the penalty shootout game."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class GoalZone(Enum):
    """Available penalty target zones.

    The solver is generic, but the penalty application starts with six zones.
    """

    TOP_LEFT = "TL"
    TOP_CENTER = "TC"
    TOP_RIGHT = "TR"
    BOTTOM_LEFT = "BL"
    BOTTOM_CENTER = "BC"
    BOTTOM_RIGHT = "BR"

    @property
    def short_label(self) -> str:
        return self.value

    @property
    def label(self) -> str:
        labels = {
            GoalZone.TOP_LEFT: "Top Left",
            GoalZone.TOP_CENTER: "Top Center",
            GoalZone.TOP_RIGHT: "Top Right",
            GoalZone.BOTTOM_LEFT: "Bottom Left",
            GoalZone.BOTTOM_CENTER: "Bottom Center",
            GoalZone.BOTTOM_RIGHT: "Bottom Right",
        }
        return labels[self]

    @classmethod
    def ordered(cls) -> tuple["GoalZone", ...]:
        return tuple(cls)


def _to_float_array(values: np.ndarray | list[float] | tuple[float, ...]) -> np.ndarray:
    return np.asarray(values, dtype=float)


@dataclass(frozen=True)
class PlayerStrategy:
    """Probability distribution over actions for one player."""

    action_labels: tuple[str, ...]
    probabilities: np.ndarray

    def __post_init__(self) -> None:
        probabilities = _to_float_array(self.probabilities)
        if probabilities.ndim != 1:
            raise ValueError("Strategy probabilities must be a one-dimensional array.")
        if len(self.action_labels) != probabilities.size:
            raise ValueError("Strategy labels and probability vector must have the same length.")
        if np.any(probabilities < -1e-12):
            raise ValueError("Strategy probabilities must be non-negative.")
        total = float(probabilities.sum())
        if not np.isclose(total, 1.0, atol=1e-8):
            raise ValueError("Strategy probabilities must sum to 1.")
        object.__setattr__(self, "probabilities", probabilities)


@dataclass(frozen=True)
class PayoffMatrix:
    """Payoff matrix from the shooter perspective.

    A[i, j] = P(score | shooter action i, goalkeeper action j).
    The goalkeeper payoff is the negative of this matrix, so the game is zero-sum.
    """

    values: np.ndarray
    row_labels: tuple[str, ...]
    column_labels: tuple[str, ...]

    def __post_init__(self) -> None:
        values = _to_float_array(self.values)
        if values.ndim != 2:
            raise ValueError("Payoff matrix must be two-dimensional.")
        rows, cols = values.shape
        if rows == 0 or cols == 0:
            raise ValueError("Payoff matrix cannot be empty.")
        if np.any(values < 0.0) or np.any(values > 1.0):
            raise ValueError("Scoring probabilities must lie in [0, 1].")
        if len(self.row_labels) != rows or len(self.column_labels) != cols:
            raise ValueError("Matrix labels must match the matrix shape.")
        object.__setattr__(self, "values", values)


@dataclass(frozen=True)
class PureStrategyAnalysis:
    """Summary of pure-strategy analysis for a zero-sum matrix game."""

    row_minima: np.ndarray
    column_maxima: np.ndarray
    maximin: float
    minimax: float
    saddle_point: tuple[int, int] | None
    saddle_point_value: float | None


@dataclass(frozen=True)
class EquilibriumValidation:
    """Validation summary for a computed mixed-strategy equilibrium."""

    row_player_payoffs: np.ndarray
    column_player_payoffs: np.ndarray
    expected_payoff: float
    game_value: float
    row_constraints_satisfied: bool
    column_constraints_satisfied: bool
    expected_value_matches: bool
    valid: bool
    messages: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EquilibriumResult:
    """Complete equilibrium solution for a finite zero-sum game."""

    shooter_strategy: PlayerStrategy
    goalkeeper_strategy: PlayerStrategy
    game_value: float
    pure_strategy_analysis: PureStrategyAnalysis
    validation: EquilibriumValidation


@dataclass(frozen=True)
class GameResult:
    shooter_zone: GoalZone
    goalkeeper_zone: GoalZone
    scoring_probability: float
    scored: bool


@dataclass(frozen=True)
class MatchStatistics:
    total_rounds: int
    shooter_goals: int = 0
    goalkeeper_saves: int = 0
    rounds_played: int = 0
    history: tuple[GameResult, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SimulationResult:
    theoretical_value: float
    observed_scoring_rate: float
    absolute_error: float
    shooter_frequencies: np.ndarray
    goalkeeper_frequencies: np.ndarray
    games_simulated: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MatchOutcome:
    shooter_goals: int
    goalkeeper_goals: int
    rounds_played: int
    sudden_death: bool
    winner: str | None
    statistics: MatchStatistics


@dataclass(frozen=True)
class TurnOutcome:
    user_zone: GoalZone
    ai_zone: GoalZone
    scored: bool
    scoring_probability: float
    round_number: int
    user_score: int
    ai_score: int
    finished: bool
    winner: str | None
    status_message: str