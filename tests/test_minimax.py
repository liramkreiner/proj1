from __future__ import annotations

import numpy as np

from game_theory.minimax import analyze_pure_strategies, column_maxima, find_saddle_point, maximin, minimax, row_minima


def test_pure_strategy_analysis_detects_saddle_point() -> None:
    matrix = np.array(
        [
            [1.0, 2.0],
            [0.0, 3.0],
        ],
        dtype=float,
    )

    analysis = analyze_pure_strategies(matrix)

    assert np.allclose(row_minima(matrix), np.array([1.0, 0.0]))
    assert np.allclose(column_maxima(matrix), np.array([1.0, 3.0]))
    assert maximin(matrix) == 1.0
    assert minimax(matrix) == 1.0
    assert find_saddle_point(matrix) == (0, 0)
    assert analysis.saddle_point_value == 1.0
    assert analysis.maximin == analysis.minimax == 1.0


def test_pure_strategy_analysis_no_saddle_point() -> None:
    matrix = np.array(
        [
            [1.0, -1.0],
            [-1.0, 1.0],
        ],
        dtype=float,
    )

    analysis = analyze_pure_strategies(matrix)

    assert analysis.saddle_point is None
    assert analysis.maximin == -1.0
    assert analysis.minimax == 1.0