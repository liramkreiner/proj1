from __future__ import annotations

import numpy as np

from game.payoff_matrix import build_default_penalty_payoff_matrix
from game_theory.nash_equilibrium import solve_nash_equilibrium, validate_equilibrium
from game_theory.mixed_strategy import solve_zero_sum_game


def test_matching_pennies_equilibrium_is_uniform() -> None:
    matrix = np.array(
        [
            [1.0, -1.0],
            [-1.0, 1.0],
        ],
        dtype=float,
    )

    solution = solve_zero_sum_game(matrix)

    assert np.allclose(solution.shooter_strategy, np.array([0.5, 0.5]))
    assert np.allclose(solution.goalkeeper_strategy, np.array([0.5, 0.5]))
    assert np.isclose(solution.game_value, 0.0)

    validation = validate_equilibrium(
        matrix,
        solution.shooter_strategy,
        solution.goalkeeper_strategy,
        solution.game_value,
    )
    assert validation.valid
    assert np.isclose(validation.expected_payoff, 0.0)


def test_non_uniform_mixed_equilibrium_matches_known_solution() -> None:
    matrix = np.array(
        [
            [4.0, 0.0],
            [2.0, 3.0],
        ],
        dtype=float,
    )

    solution = solve_zero_sum_game(matrix)

    assert np.allclose(solution.shooter_strategy, np.array([0.2, 0.8]), atol=1e-8)
    assert np.allclose(solution.goalkeeper_strategy, np.array([0.6, 0.4]), atol=1e-8)
    assert np.isclose(solution.game_value, 2.4, atol=1e-8)


def test_default_penalty_matrix_solves_and_validates() -> None:
    payoff_matrix = build_default_penalty_payoff_matrix()
    equilibrium = solve_nash_equilibrium(payoff_matrix.values)

    assert payoff_matrix.values.shape == (6, 6)
    assert np.isclose(equilibrium.shooter_strategy.probabilities.sum(), 1.0)
    assert np.isclose(equilibrium.goalkeeper_strategy.probabilities.sum(), 1.0)
    assert equilibrium.validation.valid
    assert equilibrium.game_value > 0.0