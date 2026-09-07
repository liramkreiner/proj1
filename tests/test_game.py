from __future__ import annotations

import numpy as np

from agents.human_agent import HumanAgent
from agents.optimal_agent import OptimalAgent
from game.payoff_matrix import build_default_penalty_payoff_matrix
from game.penalty_engine import PenaltyShootoutEngine, ProbabilitySampler
from game_theory.nash_equilibrium import solve_nash_equilibrium


def test_probability_sampler_rejects_invalid_distribution() -> None:
    sampler = ProbabilitySampler(np.random.default_rng(123))

    try:
        sampler.choice([], [1.0])
        raise AssertionError("Expected a failure for empty actions.")
    except ValueError:
        pass


def test_resolve_penalty_can_be_forced_to_goal() -> None:
    matrix = build_default_penalty_payoff_matrix()
    engine = PenaltyShootoutEngine(matrix, rng=np.random.default_rng(0))

    result = engine.resolve_penalty("Top Left", "Top Left")

    assert np.isclose(result.scoring_probability, matrix.values[0, 0])
    assert result.scored is False


def test_optimal_agent_samples_reproducibly() -> None:
    equilibrium = solve_nash_equilibrium(np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=float))
    agent = OptimalAgent(equilibrium.shooter_strategy)
    rng = np.random.default_rng(7)

    first = agent.choose_action(equilibrium.shooter_strategy.action_labels, rng)
    second = agent.choose_action(equilibrium.shooter_strategy.action_labels, rng)

    assert first in equilibrium.shooter_strategy.action_labels
    assert second in equilibrium.shooter_strategy.action_labels


def test_match_plays_regulation_and_sudden_death() -> None:
    matrix = build_default_penalty_payoff_matrix()
    equilibrium = solve_nash_equilibrium(matrix.values)
    shooter = OptimalAgent(equilibrium.shooter_strategy)
    goalkeeper = OptimalAgent(equilibrium.goalkeeper_strategy)
    engine = PenaltyShootoutEngine(matrix, rng=np.random.default_rng(42))

    outcome = engine.play_match(shooter, goalkeeper, total_rounds=5, sudden_death=True)

    assert outcome.rounds_played >= 5
    assert outcome.statistics.total_rounds == 5
    assert len(outcome.statistics.history) == outcome.rounds_played
    assert outcome.winner in {"Shooter", "Goalkeeper", None}


def test_human_agent_chooser_is_used() -> None:
    agent = HumanAgent(lambda actions: actions[1])
    choice = agent.choose_action(("A", "B", "C"), np.random.default_rng(0))
    assert choice == "B"