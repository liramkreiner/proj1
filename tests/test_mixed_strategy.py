"""Tests for the mixed-strategy solver against games with known solutions."""

from __future__ import annotations

import numpy as np
import pytest

from game.payoff_matrix import build_default_penalty_payoff_matrix
from game_theory.mixed_strategy import solve_zero_sum_game
from game_theory.nash_equilibrium import solve_nash_equilibrium, validate_equilibrium


def test_matching_pennies_equilibrium_is_uniform() -> None:
    matrix = np.array([[1.0, -1.0], [-1.0, 1.0]])

    solution = solve_zero_sum_game(matrix)

    assert np.allclose(solution.shooter_strategy, [0.5, 0.5])
    assert np.allclose(solution.goalkeeper_strategy, [0.5, 0.5])
    assert np.isclose(solution.game_value, 0.0)


def test_non_uniform_2x2_matches_hand_solution() -> None:
    # [[4, 0], [2, 3]]: indifference gives p = (0.2, 0.8), q = (0.6, 0.4), v = 2.4.
    matrix = np.array([[4.0, 0.0], [2.0, 3.0]])

    solution = solve_zero_sum_game(matrix)

    assert np.allclose(solution.shooter_strategy, [0.2, 0.8], atol=1e-7)
    assert np.allclose(solution.goalkeeper_strategy, [0.6, 0.4], atol=1e-7)
    assert np.isclose(solution.game_value, 2.4, atol=1e-7)


def test_rock_paper_scissors_is_uniform_with_zero_value() -> None:
    matrix = np.array([[0.0, -1.0, 1.0], [1.0, 0.0, -1.0], [-1.0, 1.0, 0.0]])

    solution = solve_zero_sum_game(matrix)

    assert np.allclose(solution.shooter_strategy, [1 / 3, 1 / 3, 1 / 3], atol=1e-7)
    assert np.allclose(solution.goalkeeper_strategy, [1 / 3, 1 / 3, 1 / 3], atol=1e-7)
    assert np.isclose(solution.game_value, 0.0, atol=1e-7)


def test_game_with_pure_saddle_point() -> None:
    # Row 2 dominates; column 1 is the keeper's best reply. Saddle value 3.
    matrix = np.array([[1.0, 2.0], [3.0, 4.0]])

    solution = solve_zero_sum_game(matrix)

    assert np.isclose(solution.game_value, 3.0, atol=1e-7)
    assert np.allclose(solution.shooter_strategy, [0.0, 1.0], atol=1e-7)
    assert np.allclose(solution.goalkeeper_strategy, [1.0, 0.0], atol=1e-7)


def test_solver_rejects_degenerate_input() -> None:
    with pytest.raises(ValueError):
        solve_zero_sum_game(np.array([1.0, 2.0]))


def test_default_penalty_matrix_solves_and_validates() -> None:
    payoff_matrix = build_default_penalty_payoff_matrix()
    equilibrium = solve_nash_equilibrium(
        payoff_matrix.values,
        row_labels=payoff_matrix.row_labels,
        column_labels=payoff_matrix.column_labels,
    )

    assert payoff_matrix.values.shape == (6, 6)
    assert np.isclose(equilibrium.shooter_strategy.probabilities.sum(), 1.0)
    assert np.isclose(equilibrium.goalkeeper_strategy.probabilities.sum(), 1.0)
    assert equilibrium.validation.valid
    # Optimal scoring probability sits strictly between maximin and minimax.
    assert equilibrium.pure_strategy_analysis.maximin < equilibrium.game_value < equilibrium.pure_strategy_analysis.minimax


def test_validation_flags_a_wrong_value() -> None:
    matrix = np.array([[1.0, -1.0], [-1.0, 1.0]])
    report = validate_equilibrium(matrix, np.array([0.5, 0.5]), np.array([0.5, 0.5]), game_value=0.9)

    assert report.valid is False


def test_equilibrium_payoff_equals_value_p_A_q() -> None:
    matrix = build_default_penalty_payoff_matrix().values
    equilibrium = solve_nash_equilibrium(matrix)

    p = equilibrium.shooter_strategy.probabilities
    q = equilibrium.goalkeeper_strategy.probabilities
    assert np.isclose(float(p @ matrix @ q), equilibrium.game_value, atol=1e-6)
