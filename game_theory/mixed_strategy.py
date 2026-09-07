"""Linear-programming solver for finite zero-sum games."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class MixedStrategySolution:
    """Primal solution for the row and column players."""

    shooter_strategy: np.ndarray
    goalkeeper_strategy: np.ndarray
    game_value: float


def _as_square_matrix(matrix: np.ndarray | Any) -> np.ndarray:
    values = np.asarray(matrix, dtype=float)
    if values.ndim != 2:
        raise ValueError("Payoff matrix must be two-dimensional.")
    rows, cols = values.shape
    if rows == 0 or cols == 0:
        raise ValueError("Payoff matrix cannot be empty.")
    if rows != cols:
        raise ValueError("Phase 1 uses square n x n zero-sum games.")
    return values


def _normalize_strategy(strategy: np.ndarray, atol: float = 1e-12) -> np.ndarray:
    clipped = np.clip(np.asarray(strategy, dtype=float), 0.0, None)
    total = float(clipped.sum())
    if total <= atol:
        raise ValueError("Solver returned an invalid probability vector.")
    return clipped / total


def _solve_row_player(matrix: np.ndarray) -> tuple[np.ndarray, float]:
    n = matrix.shape[0]
    c = np.zeros(n + 1, dtype=float)
    c[-1] = -1.0

    # Minimize -v subject to A^T p >= v 1, sum(p) = 1, p >= 0.
    # This is the LP form of max_p min_q p^T A q from the minimax theorem.
    a_ub = np.hstack([-matrix.T, np.ones((n, 1), dtype=float)])
    b_ub = np.zeros(n, dtype=float)
    a_eq = np.zeros((1, n + 1), dtype=float)
    a_eq[0, :n] = 1.0
    b_eq = np.array([1.0], dtype=float)
    bounds = [(0.0, None)] * n + [(None, None)]

    result = linprog(c, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if not result.success:
        raise RuntimeError(f"Shooter LP failed: {result.message}")

    strategy = _normalize_strategy(result.x[:n])
    game_value = float(result.x[-1])
    return strategy, game_value


def _solve_column_player(matrix: np.ndarray) -> tuple[np.ndarray, float]:
    n = matrix.shape[0]
    c = np.zeros(n + 1, dtype=float)
    c[-1] = 1.0

    # Minimize w subject to A q <= w 1, sum(q) = 1, q >= 0.
    # This is the dual LP corresponding to the same saddle-point value.
    a_ub = np.hstack([matrix, -np.ones((n, 1), dtype=float)])
    b_ub = np.zeros(n, dtype=float)
    a_eq = np.zeros((1, n + 1), dtype=float)
    a_eq[0, :n] = 1.0
    b_eq = np.array([1.0], dtype=float)
    bounds = [(0.0, None)] * n + [(None, None)]

    result = linprog(c, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if not result.success:
        raise RuntimeError(f"Goalkeeper LP failed: {result.message}")

    strategy = _normalize_strategy(result.x[:n])
    game_value = float(result.x[-1])
    return strategy, game_value


def solve_zero_sum_game(matrix: np.ndarray | Any) -> MixedStrategySolution:
    """Solve a finite zero-sum matrix game using linear programming."""

    values = _as_square_matrix(matrix)
    shooter_strategy, shooter_value = _solve_row_player(values)
    goalkeeper_strategy, goalkeeper_value = _solve_column_player(values)

    if not np.isclose(shooter_value, goalkeeper_value, atol=1e-7):
        raise RuntimeError(
            "Primal and dual LP values differ beyond tolerance: "
            f"{shooter_value:.12f} vs {goalkeeper_value:.12f}."
        )

    return MixedStrategySolution(
        shooter_strategy=shooter_strategy,
        goalkeeper_strategy=goalkeeper_strategy,
        game_value=float((shooter_value + goalkeeper_value) / 2.0),
    )