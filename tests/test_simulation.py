from __future__ import annotations

import numpy as np

from game.simulation import simulate_penalties


def test_seeded_sampling_is_reproducible() -> None:
    shooter_probs = np.array([0.2, 0.3, 0.5], dtype=float)
    goalkeeper_probs = np.array([0.1, 0.4, 0.5], dtype=float)

    rng1 = np.random.default_rng(1234)
    rng2 = np.random.default_rng(1234)

    result1 = simulate_penalties(shooter_probs, goalkeeper_probs, games=1000, rng=rng1)
    result2 = simulate_penalties(shooter_probs, goalkeeper_probs, games=1000, rng=rng2)

    assert np.allclose(result1[0], result2[0])
    assert np.allclose(result1[1], result2[1])


def test_empirical_frequencies_sum_to_one() -> None:
    shooter_probs = np.array([0.5, 0.25, 0.25], dtype=float)
    goalkeeper_probs = np.array([0.3, 0.3, 0.4], dtype=float)

    shooter_freqs, goalkeeper_freqs = simulate_penalties(
        shooter_probs,
        goalkeeper_probs,
        games=2000,
        rng=np.random.default_rng(1),
    )

    assert np.isclose(shooter_freqs.sum(), 1.0)
    assert np.isclose(goalkeeper_freqs.sum(), 1.0)