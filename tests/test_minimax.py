"""Tests for pure-strategy (maximin / minimax / saddle point) analysis."""

from __future__ import annotations

import numpy as np
import pytest

from game_theory.minimax import (
    analyze_pure_strategies,
    column_maxima,
    find_saddle_point,
    maximin,
    minimax,
    row_minima,
)


def test_saddle_point_detected_when_maximin_equals_minimax() -> None:
    matrix = np.array([[1.0, 2.0], [0.0, 3.0]])

    analysis = analyze_pure_strategies(matrix)

    assert np.allclose(row_minima(matrix), [1.0, 0.0])
    assert np.allclose(column_maxima(matrix), [1.0, 3.0])
    assert maximin(matrix) == 1.0
    assert minimax(matrix) == 1.0
    assert find_saddle_point(matrix) == (0, 0)
    assert analysis.saddle_point_value == 1.0


def test_no_saddle_point_for_matching_pennies() -> None:
    matrix = np.array([[1.0, -1.0], [-1.0, 1.0]])

    analysis = analyze_pure_strategies(matrix)

    assert analysis.saddle_point is None
    assert analysis.maximin == -1.0
    assert analysis.minimax == 1.0
    assert analysis.maximin <= analysis.minimax  # always true


def test_penalty_matrix_has_no_pure_equilibrium() -> None:
    from game.payoff_matrix import build_default_penalty_payoff_matrix

    analysis = analyze_pure_strategies(build_default_penalty_payoff_matrix().values)

    assert analysis.saddle_point is None
    assert analysis.maximin == pytest.approx(0.40)
    assert analysis.minimax == pytest.approx(0.85)


def test_rectangular_matrix_is_accepted() -> None:
    matrix = np.array([[3.0, -1.0, -3.0], [-2.0, 4.0, -1.0]])

    analysis = analyze_pure_strategies(matrix)

    assert analysis.row_minima.shape == (2,)
    assert analysis.column_maxima.shape == (3,)


def test_empty_matrix_is_rejected() -> None:
    with pytest.raises(ValueError):
        analyze_pure_strategies(np.empty((0, 0)))
