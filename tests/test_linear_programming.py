"""Tests for the raw linear-programming layer."""

from __future__ import annotations

import numpy as np
import pytest

from game_theory.linear_programming import (
    as_payoff_matrix,
    solve_column_player,
    solve_row_player,
)


def test_as_payoff_matrix_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        as_payoff_matrix(np.array([1.0, 2.0, 3.0]))  # 1-D
    with pytest.raises(ValueError):
        as_payoff_matrix(np.empty((0, 0)))  # empty
    with pytest.raises(ValueError):
        as_payoff_matrix(np.array([[1.0, np.inf], [0.0, 1.0]]))  # non-finite


def test_row_and_column_values_agree_matching_pennies() -> None:
    matrix = np.array([[1.0, -1.0], [-1.0, 1.0]])

    row = solve_row_player(matrix)
    column = solve_column_player(matrix)

    assert np.isclose(row.value, 0.0, atol=1e-9)
    assert np.isclose(column.value, 0.0, atol=1e-9)
    assert np.allclose(row.strategy, [0.5, 0.5], atol=1e-9)
    assert np.allclose(column.strategy, [0.5, 0.5], atol=1e-9)


def test_strategies_are_probability_vectors() -> None:
    matrix = np.array([[0.30, 0.85, 0.90], [0.85, 0.35, 0.85], [0.90, 0.85, 0.30]])

    for result in (solve_row_player(matrix), solve_column_player(matrix)):
        assert np.isclose(result.strategy.sum(), 1.0)
        assert np.all(result.strategy >= 0.0)


def test_shift_invariance_of_value() -> None:
    matrix = np.array([[4.0, 0.0], [2.0, 3.0]])
    shifted = matrix + 10.0

    assert np.isclose(solve_row_player(matrix).value + 10.0, solve_row_player(shifted).value, atol=1e-7)


def test_rectangular_game_is_supported() -> None:
    # 2 shooter actions, 3 goalkeeper actions.
    matrix = np.array([[3.0, -1.0, -3.0], [-2.0, 4.0, -1.0]])

    row = solve_row_player(matrix)
    column = solve_column_player(matrix)

    assert row.strategy.shape == (2,)
    assert column.strategy.shape == (3,)
    assert np.isclose(row.value, column.value, atol=1e-6)
