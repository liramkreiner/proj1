"""Pure-strategy analysis for finite zero-sum matrix games."""

from __future__ import annotations

from typing import Any

import numpy as np

from game.models import PureStrategyAnalysis


def _as_matrix(matrix: np.ndarray | Any) -> np.ndarray:
    values = np.asarray(matrix, dtype=float)
    if values.ndim != 2:
        raise ValueError("Matrix must be two-dimensional.")
    if values.shape[0] != values.shape[1]:
        raise ValueError("Phase 1 uses square n x n games.")
    return values


def row_minima(matrix: np.ndarray | Any) -> np.ndarray:
    values = _as_matrix(matrix)
    return values.min(axis=1)


def column_maxima(matrix: np.ndarray | Any) -> np.ndarray:
    values = _as_matrix(matrix)
    return values.max(axis=0)


def maximin(matrix: np.ndarray | Any) -> float:
    return float(row_minima(matrix).max())


def minimax(matrix: np.ndarray | Any) -> float:
    return float(column_maxima(matrix).min())


def find_saddle_point(matrix: np.ndarray | Any, atol: float = 1e-9) -> tuple[int, int] | None:
    values = _as_matrix(matrix)
    row_mins = values.min(axis=1)
    col_maxs = values.max(axis=0)
    maximin_value = float(row_mins.max())
    minimax_value = float(col_maxs.min())

    if not np.isclose(maximin_value, minimax_value, atol=atol):
        return None

    saddle_candidates = np.argwhere(
        np.isclose(values, maximin_value, atol=atol)
        & np.isclose(values, row_mins[:, None], atol=atol)
        & np.isclose(values, col_maxs[None, :], atol=atol)
    )
    if saddle_candidates.size == 0:
        return None
    row_index, column_index = saddle_candidates[0]
    return int(row_index), int(column_index)


def analyze_pure_strategies(matrix: np.ndarray | Any, atol: float = 1e-9) -> PureStrategyAnalysis:
    values = _as_matrix(matrix)
    row_mins = values.min(axis=1)
    col_maxs = values.max(axis=0)
    maximin_value = float(row_mins.max())
    minimax_value = float(col_maxs.min())
    saddle_point = find_saddle_point(values, atol=atol)
    saddle_point_value = float(values[saddle_point]) if saddle_point is not None else None

    return PureStrategyAnalysis(
        row_minima=row_mins,
        column_maxima=col_maxs,
        maximin=maximin_value,
        minimax=minimax_value,
        saddle_point=saddle_point,
        saddle_point_value=saddle_point_value,
    )