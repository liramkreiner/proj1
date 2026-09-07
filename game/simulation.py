"""Monte Carlo simulation utilities for the penalty shootout game."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from game.models import GoalZone, SimulationResult
from game.penalty_engine import ProbabilitySampler


def simulate_discrete_distribution(
    probabilities: Sequence[float],
    *,
    games: int,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Return empirical frequencies from repeated sampling."""

    sampler = ProbabilitySampler(rng)
    zones = tuple(GoalZone.ordered())[: len(probabilities)]
    counts = np.zeros(len(probabilities), dtype=int)
    for _ in range(games):
        choice = sampler.choice(zones, probabilities)
        counts[zones.index(choice)] += 1
    return counts / float(games)


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


def simulate_penalties(
    shooter_probabilities: Sequence[float],
    goalkeeper_probabilities: Sequence[float],
    *,
    games: int,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    sampler = ProbabilitySampler(rng)
    zones = tuple(GoalZone.ordered())[: len(shooter_probabilities)]
    shooter_counts = np.zeros(len(shooter_probabilities), dtype=int)
    goalkeeper_counts = np.zeros(len(goalkeeper_probabilities), dtype=int)
    for _ in range(games):
        shooter_choice = sampler.choice(zones, shooter_probabilities)
        goalkeeper_choice = sampler.choice(zones, goalkeeper_probabilities)
        shooter_counts[zones.index(shooter_choice)] += 1
        goalkeeper_counts[zones.index(goalkeeper_choice)] += 1
    return shooter_counts / float(games), goalkeeper_counts / float(games)