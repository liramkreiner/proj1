"""Nash equilibrium helpers for zero-sum games."""

from __future__ import annotations

from typing import Any

import numpy as np

from game.models import EquilibriumResult, EquilibriumValidation, PlayerStrategy

from .minimax import analyze_pure_strategies
from .mixed_strategy import solve_zero_sum_game


def validate_equilibrium(
    matrix: np.ndarray | Any,
    shooter_strategy: np.ndarray,
    goalkeeper_strategy: np.ndarray,
    game_value: float,
    *,
    atol: float = 1e-8,
) -> EquilibriumValidation:
    """Validate the zero-sum equilibrium conditions numerically."""

    values = np.asarray(matrix, dtype=float)
    row_player_payoffs = shooter_strategy @ values
    column_player_payoffs = values @ goalkeeper_strategy
    expected_payoff = float(shooter_strategy @ values @ goalkeeper_strategy)

    row_constraints_satisfied = bool(np.all(row_player_payoffs >= game_value - atol))
    column_constraints_satisfied = bool(np.all(column_player_payoffs <= game_value + atol))
    expected_value_matches = bool(np.isclose(expected_payoff, game_value, atol=atol))
    valid = row_constraints_satisfied and column_constraints_satisfied and expected_value_matches

    messages: list[str] = []
    if not row_constraints_satisfied:
        messages.append("Shooter optimality condition violated: p^T A should dominate the game value.")
    if not column_constraints_satisfied:
        messages.append("Goalkeeper optimality condition violated: A q should not exceed the game value.")
    if not expected_value_matches:
        messages.append("Expected payoff p^T A q does not match the computed game value.")
    if valid:
        messages.append("Equilibrium validated within numerical tolerance.")

    return EquilibriumValidation(
        row_player_payoffs=row_player_payoffs,
        column_player_payoffs=column_player_payoffs,
        expected_payoff=expected_payoff,
        game_value=float(game_value),
        row_constraints_satisfied=row_constraints_satisfied,
        column_constraints_satisfied=column_constraints_satisfied,
        expected_value_matches=expected_value_matches,
        valid=valid,
        messages=tuple(messages),
    )


def solve_nash_equilibrium(matrix: np.ndarray | Any) -> EquilibriumResult:
    """Solve and validate the mixed-strategy Nash equilibrium of a zero-sum game."""

    values = np.asarray(matrix, dtype=float)
    pure_analysis = analyze_pure_strategies(values)
    solution = solve_zero_sum_game(values)

    shooter_labels = tuple(f"Action {index + 1}" for index in range(values.shape[0]))
    goalkeeper_labels = tuple(f"Action {index + 1}" for index in range(values.shape[1]))

    shooter_strategy = PlayerStrategy(shooter_labels, solution.shooter_strategy)
    goalkeeper_strategy = PlayerStrategy(goalkeeper_labels, solution.goalkeeper_strategy)
    validation = validate_equilibrium(
        values,
        shooter_strategy.probabilities,
        goalkeeper_strategy.probabilities,
        solution.game_value,
    )

    return EquilibriumResult(
        shooter_strategy=shooter_strategy,
        goalkeeper_strategy=goalkeeper_strategy,
        game_value=solution.game_value,
        pure_strategy_analysis=pure_analysis,
        validation=validation,
    )