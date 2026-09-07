"""Penalty shootout resolution and match logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from agents.base_agent import BaseAgent
from game.models import GameResult, GoalZone, MatchOutcome, MatchStatistics, PayoffMatrix


def validate_probability_distribution(probabilities: Sequence[float], *, atol: float = 1e-8) -> np.ndarray:
    values = np.asarray(probabilities, dtype=float)
    if values.ndim != 1:
        raise ValueError("Probability distribution must be one-dimensional.")
    if np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("Probabilities must lie in [0, 1].")
    total = float(values.sum())
    if not np.isclose(total, 1.0, atol=atol):
        raise ValueError("Probability distribution must sum to 1.")
    return values


class ProbabilitySampler:
    """Sample actions from a validated discrete probability distribution."""

    def __init__(self, rng: np.random.Generator | None = None) -> None:
        self._rng = rng if rng is not None else np.random.default_rng()

    @property
    def rng(self) -> np.random.Generator:
        return self._rng

    def choice(self, actions: Sequence[GoalZone], probabilities: Sequence[float]) -> GoalZone:
        validated = validate_probability_distribution(probabilities)
        if len(actions) == 0:
            raise ValueError("At least one action is required for sampling.")
        index = int(self._rng.choice(len(actions), p=validated))
        return actions[index]


@dataclass(frozen=True)
class PenaltyOutcome:
    """Single penalty outcome with the action pair and score event."""

    result: GameResult
    shooter_label: str
    goalkeeper_label: str


class PenaltyShootoutEngine:
    """Resolve penalties using a payoff matrix and seeded random sampling."""

    def __init__(self, payoff_matrix: PayoffMatrix, rng: np.random.Generator | None = None) -> None:
        self._payoff_matrix = payoff_matrix
        self._zones = list(GoalZone.ordered())
        if payoff_matrix.row_labels != tuple(zone.label for zone in self._zones):
            raise ValueError("The current engine expects the default GoalZone ordering.")
        self._rng = rng if rng is not None else np.random.default_rng()
        self._sampler = ProbabilitySampler(self._rng)

    @property
    def payoff_matrix(self) -> PayoffMatrix:
        return self._payoff_matrix

    def _coerce_zone(self, value: GoalZone | str) -> GoalZone:
        if isinstance(value, GoalZone):
            return value
        normalized = value.replace(" ", "_").replace("-", "_").upper()
        try:
            return GoalZone[normalized]
        except KeyError as exc:
            for zone in GoalZone:
                if value == zone.label or value == zone.short_label:
                    return zone
            raise ValueError(f"Unknown goal zone: {value}") from exc

    def resolve_penalty(self, shooter_zone: GoalZone | str, goalkeeper_zone: GoalZone | str) -> GameResult:
        shooter_zone = self._coerce_zone(shooter_zone)
        goalkeeper_zone = self._coerce_zone(goalkeeper_zone)
        row_index = self._zones.index(shooter_zone)
        column_index = self._zones.index(goalkeeper_zone)
        scoring_probability = float(self._payoff_matrix.values[row_index, column_index])
        scored = bool(self._rng.random() < scoring_probability)
        return GameResult(
            shooter_zone=shooter_zone,
            goalkeeper_zone=goalkeeper_zone,
            scoring_probability=scoring_probability,
            scored=scored,
        )

    def play_penalty(self, shooter_agent: BaseAgent, goalkeeper_agent: BaseAgent) -> PenaltyOutcome:
        zone_labels = tuple(zone.label for zone in self._zones)
        shooter_choice = shooter_agent.choose_action(zone_labels, self._rng)
        goalkeeper_choice = goalkeeper_agent.choose_action(zone_labels, self._rng)
        shooter_zone = GoalZone[shooter_choice.replace(" ", "_").upper()]
        goalkeeper_zone = GoalZone[goalkeeper_choice.replace(" ", "_").upper()]
        result = self.resolve_penalty(shooter_zone, goalkeeper_zone)
        return PenaltyOutcome(result=result, shooter_label=shooter_choice, goalkeeper_label=goalkeeper_choice)

    def play_match(
        self,
        shooter_agent: BaseAgent,
        goalkeeper_agent: BaseAgent,
        *,
        total_rounds: int = 5,
        sudden_death: bool = True,
    ) -> MatchOutcome:
        shooter_goals = 0
        goalkeeper_goals = 0
        history: list[GameResult] = []

        for _ in range(total_rounds):
            outcome = self.play_penalty(shooter_agent, goalkeeper_agent).result
            history.append(outcome)
            if outcome.scored:
                shooter_goals += 1
            else:
                goalkeeper_goals += 1

        rounds_played = total_rounds
        if shooter_goals == goalkeeper_goals and sudden_death:
            while shooter_goals == goalkeeper_goals:
                outcome = self.play_penalty(shooter_agent, goalkeeper_agent).result
                history.append(outcome)
                rounds_played += 1
                if outcome.scored:
                    shooter_goals += 1
                else:
                    goalkeeper_goals += 1
                if shooter_goals != goalkeeper_goals:
                    break

        winner: str | None
        if shooter_goals > goalkeeper_goals:
            winner = "Shooter"
        elif goalkeeper_goals > shooter_goals:
            winner = "Goalkeeper"
        else:
            winner = None

        statistics = MatchStatistics(
            total_rounds=total_rounds,
            shooter_goals=shooter_goals,
            goalkeeper_saves=goalkeeper_goals,
            rounds_played=rounds_played,
            history=tuple(history),
        )
        return MatchOutcome(
            shooter_goals=shooter_goals,
            goalkeeper_goals=goalkeeper_goals,
            rounds_played=rounds_played,
            sudden_death=rounds_played > total_rounds,
            winner=winner,
            statistics=statistics,
        )