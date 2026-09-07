"""Tests for the core dataclasses and the GoalZone enum."""

from __future__ import annotations

import numpy as np
import pytest

from game.models import GoalZone, PlayerStrategy


def test_goalzone_ordering_and_labels() -> None:
    zones = GoalZone.ordered()
    assert len(zones) == 6
    assert zones[0] is GoalZone.TOP_LEFT
    assert GoalZone.TOP_LEFT.short_label == "TL"
    assert GoalZone.BOTTOM_RIGHT.label == "Bottom Right"


def test_player_strategy_accepts_valid_distribution() -> None:
    strategy = PlayerStrategy(("A", "B", "C"), np.array([0.2, 0.3, 0.5]))
    assert np.isclose(strategy.probabilities.sum(), 1.0)


@pytest.mark.parametrize(
    "probabilities",
    [
        np.array([0.2, 0.3, 0.4]),   # sums to 0.9
        np.array([-0.1, 0.6, 0.5]),  # negative entry
    ],
)
def test_player_strategy_rejects_invalid_distribution(probabilities: np.ndarray) -> None:
    with pytest.raises(ValueError):
        PlayerStrategy(("A", "B", "C"), probabilities)


def test_player_strategy_rejects_label_length_mismatch() -> None:
    with pytest.raises(ValueError):
        PlayerStrategy(("A", "B"), np.array([0.2, 0.3, 0.5]))
