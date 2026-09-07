"""Nash equilibrium for zero-sum games, with a numerical validation report.

For a finite **zero-sum** game the minimax solution *is* a Nash equilibrium:
if ``(p*, q*)`` solves ``max_p min_q p^T A q = min_q max_p p^T A q = v`` then
neither player can gain by deviating unilaterally, which is exactly the Nash
condition.  So the linear-programming solution from
:mod:`game_theory.mixed_strategy` gives us the equilibrium directly; this
module only wraps it, attaches the pure-strategy analysis, and checks the
equilibrium inequalities hold numerically.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from game.models import (
    EquilibriumResult,
    EquilibriumValidation,
    PlayerStrategy,
    PureStrategyAnalysis,
)

from .minimax import analyze_pure_strategies
from .mixed_strategy import solve_zero_sum_game

__all__ = ["solve_nash_equilibrium", "validate_equilibrium"]

# LP output on a 6x6 matrix is good to ~1e-7; 1e-6 is a safe validation band.
_VALIDATION_ATOL = 1e-6


def validate_equilibrium(
    matrix: np.ndarray | Any,
    shooter_strategy: np.ndarray,
    goalkeeper_strategy: np.ndarray,
    game_value: float,
    *,
    atol: float = _VALIDATION_ATOL,
) -> EquilibriumValidation:
    """Check the equilibrium inequalities numerically.

    With ``A`` the shooter payoff matrix and value ``v`` the conditions are

        (p^T A)_j >= v - atol    for every goalkeeper column j
        (A q)_i   <= v + atol    for every shooter row i
        p^T A q   ~= v

    The first says the shooter secures at least ``v`` against any keeper reply;
    the second says the keeper concedes at most ``v`` against any shot.
    Together with the equality they certify a saddle point.
    """

    values = np.asarray(matrix, dtype=float)
    p = np.asarray(shooter_strategy, dtype=float)
    q = np.asarray(goalkeeper_strategy, dtype=float)

    row_player_payoffs = p @ values          # length n: shooter payoff vs each keeper column
    column_player_payoffs = values @ q       # length m: shooter payoff for each shot row
    expected_payoff = float(p @ values @ q)

    row_ok = bool(np.all(row_player_payoffs >= game_value - atol))
    col_ok = bool(np.all(column_player_payoffs <= game_value + atol))
    value_ok = bool(np.isclose(expected_payoff, game_value, atol=atol))
    valid = row_ok and col_ok and value_ok

    messages: list[str] = []
    messages.append(
        f"Shooter security check  min(pᵀA) = {row_player_payoffs.min():.6f} "
        f"{'>=' if row_ok else '<'} v - tol ({game_value - atol:.6f})"
    )
    messages.append(
        f"Keeper ceiling check    max(Aq)  = {column_player_payoffs.max():.6f} "
        f"{'<=' if col_ok else '>'} v + tol ({game_value + atol:.6f})"
    )
    messages.append(
        f"Value consistency       pᵀAq = {expected_payoff:.6f} vs v = {game_value:.6f} "
        f"(|Δ| = {abs(expected_payoff - game_value):.2e})"
    )
    messages.append("Equilibrium VALID within tolerance." if valid else "Equilibrium INVALID — see checks above.")

    return EquilibriumValidation(
        row_player_payoffs=row_player_payoffs,
        column_player_payoffs=column_player_payoffs,
        expected_payoff=expected_payoff,
        game_value=float(game_value),
        row_constraints_satisfied=row_ok,
        column_constraints_satisfied=col_ok,
        expected_value_matches=value_ok,
        valid=valid,
        messages=tuple(messages),
    )


def _default_labels(prefix: str, count: int) -> tuple[str, ...]:
    return tuple(f"{prefix} {i + 1}" for i in range(count))


def solve_nash_equilibrium(
    matrix: np.ndarray | Any,
    *,
    row_labels: Sequence[str] | None = None,
    column_labels: Sequence[str] | None = None,
) -> EquilibriumResult:
    """Solve and validate the mixed-strategy Nash equilibrium of a zero-sum game."""

    values = np.asarray(matrix, dtype=float)
    n_rows, n_cols = values.shape

    pure_analysis: PureStrategyAnalysis = analyze_pure_strategies(values)
    solution = solve_zero_sum_game(values)

    shooter_labels = tuple(row_labels) if row_labels is not None else _default_labels("Shot", n_rows)
    goalkeeper_labels = tuple(column_labels) if column_labels is not None else _default_labels("Dive", n_cols)

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
