"""Monte Carlo simulation tests: reproducibility and convergence to theory."""

from __future__ import annotations

import numpy as np
import pytest

from game.payoff_matrix import build_default_penalty_payoff_matrix
from game.simulation import run_penalty_monte_carlo, simulate_penalties
from game_theory.nash_equilibrium import solve_nash_equilibrium


def test_seeded_sampling_is_reproducible() -> None:
    shooter_probs = np.array([0.2, 0.3, 0.5])
    goalkeeper_probs = np.array([0.1, 0.4, 0.5])

    result1 = simulate_penalties(shooter_probs, goalkeeper_probs, games=1000, rng=np.random.default_rng(1234))
    result2 = simulate_penalties(shooter_probs, goalkeeper_probs, games=1000, rng=np.random.default_rng(1234))

    assert np.allclose(result1[0], result2[0])
    assert np.allclose(result1[1], result2[1])


def test_empirical_frequencies_sum_to_one() -> None:
    shooter_freqs, goalkeeper_freqs = simulate_penalties(
        np.array([0.5, 0.25, 0.25]),
        np.array([0.3, 0.3, 0.4]),
        games=2000,
        rng=np.random.default_rng(1),
    )
    assert np.isclose(shooter_freqs.sum(), 1.0)
    assert np.isclose(goalkeeper_freqs.sum(), 1.0)


def test_monte_carlo_is_reproducible_with_seed() -> None:
    matrix = build_default_penalty_payoff_matrix().values
    equilibrium = solve_nash_equilibrium(matrix)
    p = equilibrium.shooter_strategy.probabilities
    q = equilibrium.goalkeeper_strategy.probabilities

    a = run_penalty_monte_carlo(matrix, p, q, games=5000, seed=7)
    b = run_penalty_monte_carlo(matrix, p, q, games=5000, seed=7)

    assert a.observed_scoring_rate == b.observed_scoring_rate
    assert np.array_equal(a.shooter_frequencies, b.shooter_frequencies)


def test_monte_carlo_converges_to_game_value_and_strategies() -> None:
    matrix = build_default_penalty_payoff_matrix().values
    equilibrium = solve_nash_equilibrium(matrix)
    p = equilibrium.shooter_strategy.probabilities
    q = equilibrium.goalkeeper_strategy.probabilities

    result = run_penalty_monte_carlo(matrix, p, q, games=200_000, seed=2024)

    # Observed scoring rate approaches the theoretical game value.
    assert result.absolute_error < 5e-3
    # Empirical action frequencies approach the equilibrium mixed strategies.
    assert np.allclose(result.shooter_frequencies, p, atol=1e-2)
    assert np.allclose(result.goalkeeper_frequencies, q, atol=1e-2)


def test_monte_carlo_rejects_bad_arguments() -> None:
    matrix = build_default_penalty_payoff_matrix().values
    p = np.full(6, 1 / 6)
    with pytest.raises(ValueError):
        run_penalty_monte_carlo(matrix, p, p, games=0)
    with pytest.raises(ValueError):
        run_penalty_monte_carlo(matrix, np.full(3, 1 / 3), p, games=10)
