"""Linear-programming formulation of finite two-player zero-sum games.

This module contains the *pure* optimisation layer: given a payoff matrix
``A`` (rows = shooter/maximiser actions, columns = goalkeeper/minimiser
actions, entry ``A[i, j] = P(score | i, j)``) it returns the optimal mixed
strategies and the game value.

Why linear programming solves the game (von Neumann minimax theorem)
-------------------------------------------------------------------
The shooter picks a probability vector ``p`` over rows, the goalkeeper a
probability vector ``q`` over columns.  The shooter's expected payoff is
``p^T A q``.  The minimax theorem states that for a finite zero-sum game

    max_p min_q  p^T A q  =  min_q max_p  p^T A q  =  v

and ``v`` is the *value* of the game.

Fix the shooter's strategy ``p``.  The goalkeeper, minimising, will always
put all weight on the column with the smallest ``(p^T A)_j``.  Hence

    min_q p^T A q = min_j (p^T A)_j .

The shooter therefore wants to solve

    maximise   v
    subject to (p^T A)_j >= v      for every column j        (1)
               sum_i p_i = 1
               p_i >= 0 .

Constraint (1) says "whatever pure column the goalkeeper replies with, the
shooter still earns at least ``v``"; maximising ``v`` pushes it up to the
security level ``max_p min_j (p^T A)_j``, which the minimax theorem equates
with the game value.  This is a linear program in the variables
``(p_1, ..., p_m, v)`` and is what :func:`solve_row_player` builds.

The goalkeeper's problem is the symmetric (dual) LP

    minimise   w
    subject to (A q)_i <= w        for every row i
               sum_j q_j = 1
               q_j >= 0 ,

built by :func:`solve_column_player`.  LP strong duality guarantees the two
optimal objective values coincide, and that common number is ``v``.

We solve both programs explicitly and cross-check their objective values;
that check is a numerical proof that we really found the saddle point.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linprog

__all__ = [
    "LinearProgramResult",
    "as_payoff_matrix",
    "solve_row_player",
    "solve_column_player",
]

# scipy's HiGHS backend; deterministic and exact for these small dense LPs.
_LINPROG_METHOD = "highs"


@dataclass(frozen=True)
class LinearProgramResult:
    """Outcome of one player's linear program.

    Attributes
    ----------
    strategy:
        Optimal mixed strategy as a probability vector (non-negative, sums to 1).
    value:
        Optimal objective value of the linear program.  For a consistent
        payoff matrix the row player's value equals the column player's value
        and both equal the game value ``v``.
    """

    strategy: np.ndarray
    value: float


def as_payoff_matrix(matrix: np.ndarray | Any) -> np.ndarray:
    """Validate and coerce ``matrix`` into a 2-D float array.

    Rectangular (``m x n``) matrices are allowed; the solver is fully general.
    """

    values = np.asarray(matrix, dtype=float)
    if values.ndim != 2:
        raise ValueError("Payoff matrix must be two-dimensional.")
    if values.size == 0:
        raise ValueError("Payoff matrix cannot be empty.")
    if not np.all(np.isfinite(values)):
        raise ValueError("Payoff matrix must contain only finite numbers.")
    return values


def _normalise(vector: np.ndarray, *, atol: float = 1e-9) -> np.ndarray:
    """Clip tiny negatives from a solver result and renormalise to sum 1."""

    clipped = np.clip(np.asarray(vector, dtype=float), 0.0, None)
    clipped[clipped < atol] = 0.0
    total = float(clipped.sum())
    if total <= atol:
        raise RuntimeError("Linear program returned a degenerate probability vector.")
    return clipped / total


def _shift_to_positive(matrix: np.ndarray) -> tuple[np.ndarray, float]:
    """Add a constant so every entry is >= 1.

    ``linprog`` needs a bounded objective.  Shifting the whole matrix by a
    constant ``c`` adds exactly ``c`` to the game value and leaves both
    optimal strategies unchanged (``p^T (A + c) q = p^T A q + c`` for any
    distributions ``p, q``).  We undo the shift on the returned value.
    """

    minimum = float(matrix.min())
    shift = 0.0
    if minimum <= 0.0:
        shift = 1.0 - minimum
    return matrix + shift, shift


def solve_row_player(matrix: np.ndarray | Any) -> LinearProgramResult:
    """Solve the shooter's (row / maximiser) linear program.

    Variables ``x = [p_1, ..., p_m, v]``.  ``linprog`` minimises, so we
    minimise ``-v``.  Constraints, all written as ``<=``:

    * ``-(A^T)_j . p + v <= 0``  for every column ``j``   (i.e. ``p^T A >= v``)
    * ``sum_i p_i = 1``
    * ``p_i >= 0``, ``v`` free.
    """

    values = as_payoff_matrix(matrix)
    shifted, shift = _shift_to_positive(values)
    n_rows, n_cols = shifted.shape

    c = np.zeros(n_rows + 1)
    c[-1] = -1.0  # minimise -v  <=>  maximise v

    a_ub = np.hstack([-shifted.T, np.ones((n_cols, 1))])
    b_ub = np.zeros(n_cols)

    a_eq = np.zeros((1, n_rows + 1))
    a_eq[0, :n_rows] = 1.0
    b_eq = np.array([1.0])

    bounds = [(0.0, None)] * n_rows + [(None, None)]

    result = linprog(c, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=b_eq, bounds=bounds, method=_LINPROG_METHOD)
    if not result.success:
        raise RuntimeError(f"Shooter linear program failed: {result.message}")

    strategy = _normalise(result.x[:n_rows])
    value = float(result.x[-1]) - shift
    return LinearProgramResult(strategy=strategy, value=value)


def solve_column_player(matrix: np.ndarray | Any) -> LinearProgramResult:
    """Solve the goalkeeper's (column / minimiser) linear program.

    Variables ``y = [q_1, ..., q_n, w]``.  Minimise ``w``.  Constraints:

    * ``(A)_i . q - w <= 0``  for every row ``i``           (i.e. ``A q <= w``)
    * ``sum_j q_j = 1``
    * ``q_j >= 0``, ``w`` free.
    """

    values = as_payoff_matrix(matrix)
    shifted, shift = _shift_to_positive(values)
    n_rows, n_cols = shifted.shape

    c = np.zeros(n_cols + 1)
    c[-1] = 1.0  # minimise w

    a_ub = np.hstack([shifted, -np.ones((n_rows, 1))])
    b_ub = np.zeros(n_rows)

    a_eq = np.zeros((1, n_cols + 1))
    a_eq[0, :n_cols] = 1.0
    b_eq = np.array([1.0])

    bounds = [(0.0, None)] * n_cols + [(None, None)]

    result = linprog(c, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=b_eq, bounds=bounds, method=_LINPROG_METHOD)
    if not result.success:
        raise RuntimeError(f"Goalkeeper linear program failed: {result.message}")

    strategy = _normalise(result.x[:n_cols])
    value = float(result.x[-1]) - shift
    return LinearProgramResult(strategy=strategy, value=value)
