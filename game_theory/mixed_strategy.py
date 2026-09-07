"""Mixed-strategy solver for finite zero-sum games.

This is the orchestration layer on top of :mod:`game_theory.linear_programming`.
It solves both the row-player and column-player linear programs, cross-checks
that their optimal objective values agree (LP strong duality => a genuine
saddle point was found), and packages the result.

The solver is fully general: it accepts any ``m x n`` payoff matrix, not just
square or ``2 x 2`` games.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .linear_programming import as_payoff_matrix, solve_column_player, solve_row_player

__all__ = ["MixedStrategySolution", "solve_zero_sum_game"]

# Row-player and column-player LP objectives must match to this tolerance.
_DUALITY_ATOL = 1e-6


@dataclass(frozen=True)
class MixedStrategySolution:
    """Optimal mixed strategies and value of a zero-sum game.

    ``shooter_strategy`` maximises the guaranteed expected score; the
    goalkeeper's payoff is ``-A`` so ``goalkeeper_strategy`` minimises it.
    ``game_value`` is ``v = p^T A q`` under optimal play.
    """

    shooter_strategy: np.ndarray
    goalkeeper_strategy: np.ndarray
    game_value: float


def solve_zero_sum_game(matrix: np.ndarray | Any) -> MixedStrategySolution:
    """Solve a finite zero-sum matrix game by linear programming.

    Raises
    ------
    ValueError
        If ``matrix`` is not a finite 2-D array.
    RuntimeError
        If either linear program fails or the two objective values disagree
        beyond :data:`_DUALITY_ATOL` (which would mean the numerics are
        untrustworthy).
    """

    values = as_payoff_matrix(matrix)

    row_result = solve_row_player(values)
    column_result = solve_column_player(values)

    if not np.isclose(row_result.value, column_result.value, atol=_DUALITY_ATOL):
        raise RuntimeError(
            "Row-player and column-player LP values disagree: "
            f"{row_result.value:.12f} vs {column_result.value:.12f}. "
            "The minimax solution is numerically unreliable for this matrix."
        )

    game_value = 0.5 * (row_result.value + column_result.value)
    return MixedStrategySolution(
        shooter_strategy=row_result.strategy,
        goalkeeper_strategy=column_result.strategy,
        game_value=float(game_value),
    )
