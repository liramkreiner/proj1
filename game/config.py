"""Central configuration for the penalty game's geometry and defaults.

Everything that is *tunable* about the game lives here so it is never
hard-coded in the engine, the solver, or the UI.

Changing the number of zones
----------------------------
The game-theory layer (``game_theory``) is already fully general over any
``m x n`` payoff matrix.  To move from the default 6 zones to, say, 9:

1. Extend :class:`~game.models.GoalZone` with the new members.
2. Provide a matching ``GRID_ROWS x GRID_COLS`` probability matrix in
   :mod:`game.payoff_matrix`.
3. Update :data:`GRID_ROWS` / :data:`GRID_COLS` below.

No other code needs to change: the LP solver, the Monte Carlo engine and the
match controller all read the zone list and matrix shape dynamically.
"""

from __future__ import annotations

from dataclasses import dataclass

# Goal-mouth grid used by the default model and the UI renderer.
GRID_ROWS: int = 2          # top / bottom
GRID_COLS: int = 3          # left / centre / right

DEFAULT_ROUNDS_PER_SIDE: int = 5
DEFAULT_MONTE_CARLO_GAMES: int = 10_000
MAX_MONTE_CARLO_GAMES: int = 2_000_000

# Numerical tolerances shared across the project.
PROBABILITY_SUM_ATOL: float = 1e-8
EQUILIBRIUM_ATOL: float = 1e-6


@dataclass(frozen=True)
class MatchRules:
    """Rules for a single shootout."""

    rounds_per_side: int = DEFAULT_ROUNDS_PER_SIDE
    sudden_death: bool = True

    def __post_init__(self) -> None:
        if self.rounds_per_side < 1:
            raise ValueError("A shootout needs at least one round per side.")
