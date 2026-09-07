"""Tests for the agent layer, especially that the AI is genuinely randomised."""

from __future__ import annotations

import numpy as np
import pytest

from agents.human_agent import HumanAgent
from agents.optimal_agent import OptimalAgent
from game.models import PlayerStrategy
from game.payoff_matrix import build_default_penalty_payoff_matrix
from game_theory.nash_equilibrium import solve_nash_equilibrium


def _equilibrium_shooter_strategy() -> PlayerStrategy:
    matrix = build_default_penalty_payoff_matrix()
    return solve_nash_equilibrium(
        matrix.values, row_labels=matrix.row_labels, column_labels=matrix.column_labels
    ).shooter_strategy


def test_optimal_agent_samples_whole_support_not_the_argmax() -> None:
    strategy = _equilibrium_shooter_strategy()
    agent = OptimalAgent(strategy)
    rng = np.random.default_rng(0)

    picks = [agent.choose_action(strategy.action_labels, rng) for _ in range(4000)]
    distinct = set(picks)

    # A greedy "pick the best zone" AI would only ever return one label.
    assert len(distinct) == len(strategy.action_labels)


def test_optimal_agent_empirical_mix_matches_strategy() -> None:
    strategy = _equilibrium_shooter_strategy()
    agent = OptimalAgent(strategy)
    rng = np.random.default_rng(123)
    labels = list(strategy.action_labels)

    counts = np.zeros(len(labels))
    for _ in range(20000):
        counts[labels.index(agent.choose_action(strategy.action_labels, rng))] += 1
    frequencies = counts / counts.sum()

    assert np.allclose(frequencies, strategy.probabilities, atol=2e-2)


def test_optimal_agent_is_reproducible_under_seed() -> None:
    strategy = _equilibrium_shooter_strategy()
    labels = strategy.action_labels
    seq1 = [OptimalAgent(strategy).choose_action(labels, np.random.default_rng(9)) for _ in range(1)]
    seq2 = [OptimalAgent(strategy).choose_action(labels, np.random.default_rng(9)) for _ in range(1)]
    assert seq1 == seq2


def test_optimal_agent_rejects_mismatched_label_count() -> None:
    strategy = _equilibrium_shooter_strategy()
    with pytest.raises(ValueError):
        OptimalAgent(strategy).choose_action(("only", "two"), np.random.default_rng(0))


def test_human_agent_uses_injected_chooser() -> None:
    agent = HumanAgent(lambda actions: actions[2])
    assert agent.choose_action(("A", "B", "C"), np.random.default_rng(0)) == "C"

    with pytest.raises(ValueError):
        HumanAgent(lambda actions: "Z").choose_action(("A", "B"), np.random.default_rng(0))
