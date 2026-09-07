"""Tests for the penalty probability model and payoff-matrix generation."""

from __future__ import annotations

import numpy as np
import pytest

from game.models import GoalZone, PayoffMatrix
from game.payoff_matrix import (
    DEFAULT_PENALTY_PROBABILITIES,
    PenaltyProbabilityModel,
    build_default_penalty_payoff_matrix,
    build_payoff_matrix,
    default_penalty_probability_model,
)


def test_default_matrix_has_expected_shape_and_labels() -> None:
    matrix = build_default_penalty_payoff_matrix()

    assert matrix.values.shape == (6, 6)
    assert matrix.row_labels == tuple(zone.label for zone in GoalZone)
    assert matrix.column_labels == tuple(zone.label for zone in GoalZone)


def test_all_scoring_probabilities_are_valid() -> None:
    values = build_default_penalty_payoff_matrix().values

    assert np.all(values >= 0.0)
    assert np.all(values <= 1.0)


def test_diagonal_is_the_low_scoring_case() -> None:
    # Keeper guesses the shot zone: scoring probability must be the row minimum.
    values = build_default_penalty_payoff_matrix().values
    for i in range(6):
        assert values[i, i] == values[i].min()


def test_payoff_matrix_is_generated_from_the_model_unchanged() -> None:
    model = default_penalty_probability_model()
    built = build_payoff_matrix(model)

    assert np.array_equal(built.values, DEFAULT_PENALTY_PROBABILITIES)


def test_model_rejects_probabilities_outside_unit_interval() -> None:
    bad = DEFAULT_PENALTY_PROBABILITIES.copy()
    bad[0, 0] = 1.5
    with pytest.raises(ValueError):
        PenaltyProbabilityModel(bad, GoalZone.ordered(), GoalZone.ordered())


def test_model_rejects_mismatched_zone_count() -> None:
    with pytest.raises(ValueError):
        PenaltyProbabilityModel(DEFAULT_PENALTY_PROBABILITIES.copy(), GoalZone.ordered()[:3], GoalZone.ordered())


def test_payoff_matrix_rejects_out_of_range_values() -> None:
    with pytest.raises(ValueError):
        PayoffMatrix(np.array([[0.5, 1.2], [0.3, 0.4]]), ("a", "b"), ("c", "d"))
