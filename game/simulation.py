"""Monte Carlo simulation for the penalty shootout zero-sum game.

The purpose of this module is the Phase 1 -> Phase 5 bridge: it lets us
*empirically* confirm the theory.  If both players sample from their optimal
mixed strategies ``p`` and ``q``, the long-run scoring rate must converge to
the game value ``v = p^T A q`` and the observed action frequencies must
converge to ``p`` and ``q`` themselves (law of large numbers).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from game.models import GoalZone, SimulationResult
from game.penalty_engine import ProbabilitySampler, validate_probability_distribution

__all__ = [
    "simulate_discrete_distribution",
    "simulate_penalties",
    "summarize_simulation",
    "run_penalty_monte_carlo",
]


def simulate_discrete_distribution(
    probabilities: Sequence[float],
    *,
    games: int,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Return empirical frequencies from repeated sampling of one distribution."""

    sampler = ProbabilitySampler(rng)
    zones = tuple(GoalZone.ordered())[: len(probabilities)]
    counts = np.zeros(len(probabilities), dtype=int)
    for _ in range(games):
        choice = sampler.choice(zones, probabilities)
        counts[zones.index(choice)] += 1
    return counts / float(games)


def simulate_penalties(
    shooter_probabilities: Sequence[float],
    goalkeeper_probabilities: Sequence[float],
    *,
    games: int,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return empirical (shooter, goalkeeper) action frequencies."""

    sampler = ProbabilitySampler(rng)
    zones = tuple(GoalZone.ordered())[: len(shooter_probabilities)]
    shooter_counts = np.zeros(len(shooter_probabilities), dtype=int)
    goalkeeper_counts = np.zeros(len(goalkeeper_probabilities), dtype=int)
    for _ in range(games):
        shooter_counts[zones.index(sampler.choice(zones, shooter_probabilities))] += 1
        goalkeeper_counts[zones.index(sampler.choice(zones, goalkeeper_probabilities))] += 1
    return shooter_counts / float(games), goalkeeper_counts / float(games)


def summarize_simulation(
    *,
    theoretical_value: float,
    observed_scoring_rate: float,
    shooter_frequencies: np.ndarray,
    goalkeeper_frequencies: np.ndarray,
    games_simulated: int,
) -> SimulationResult:
    return SimulationResult(
        theoretical_value=theoretical_value,
        observed_scoring_rate=observed_scoring_rate,
        absolute_error=abs(observed_scoring_rate - theoretical_value),
        shooter_frequencies=shooter_frequencies,
        goalkeeper_frequencies=goalkeeper_frequencies,
        games_simulated=games_simulated,
    )


def run_penalty_monte_carlo(
    payoff_matrix: np.ndarray,
    shooter_probabilities: Sequence[float],
    goalkeeper_probabilities: Sequence[float],
    *,
    games: int,
    theoretical_value: float | None = None,
    seed: int | None = None,
) -> SimulationResult:
    """Simulate ``games`` penalties with both players using mixed strategies.

    Vectorised: all shooter picks, keeper picks and score coin-flips are drawn
    in three array operations, so 100k+ games run in milliseconds.

    Parameters
    ----------
    payoff_matrix:
        ``A[i, j] = P(score | shot i, dive j)``.
    shooter_probabilities, goalkeeper_probabilities:
        Mixed strategies to sample from (typically the Nash equilibrium).
    games:
        Number of independent penalties.
    theoretical_value:
        The game value ``v`` to compare against.  Defaults to
        ``p^T A q`` computed from the supplied strategies.
    seed:
        Seed for the ``numpy`` Generator, for reproducible runs.
    """

    if games <= 0:
        raise ValueError("Number of games must be a positive integer.")

    matrix = np.asarray(payoff_matrix, dtype=float)
    p = validate_probability_distribution(shooter_probabilities)
    q = validate_probability_distribution(goalkeeper_probabilities)
    n_rows, n_cols = matrix.shape
    if p.size != n_rows or q.size != n_cols:
        raise ValueError("Strategy lengths must match the payoff-matrix dimensions.")

    if theoretical_value is None:
        theoretical_value = float(p @ matrix @ q)

    rng = np.random.default_rng(seed)
    shooter_picks = rng.choice(n_rows, size=games, p=p)
    goalkeeper_picks = rng.choice(n_cols, size=games, p=q)

    scoring_probabilities = matrix[shooter_picks, goalkeeper_picks]
    scored = rng.random(games) < scoring_probabilities
    observed_scoring_rate = float(scored.mean())

    shooter_frequencies = np.bincount(shooter_picks, minlength=n_rows) / games
    goalkeeper_frequencies = np.bincount(goalkeeper_picks, minlength=n_cols) / games

    return SimulationResult(
        theoretical_value=float(theoretical_value),
        observed_scoring_rate=observed_scoring_rate,
        absolute_error=abs(observed_scoring_rate - float(theoretical_value)),
        shooter_frequencies=shooter_frequencies,
        goalkeeper_frequencies=goalkeeper_frequencies,
        games_simulated=games,
        metadata={
            "seed": seed,
            "shooter_l1_error": float(np.abs(shooter_frequencies - p).sum()),
            "goalkeeper_l1_error": float(np.abs(goalkeeper_frequencies - q).sum()),
        },
    )
