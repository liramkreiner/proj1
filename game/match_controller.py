"""Pure-Python match controller used by the Qt UI.

The controller owns the game flow, role switching, score tracking, and the
optimal mixed-strategy AI. The GUI only renders the state and forwards user
actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from game.models import EquilibriumResult, GoalZone, PayoffMatrix, TurnOutcome
from game.payoff_matrix import build_default_penalty_payoff_matrix
from game.penalty_engine import PenaltyShootoutEngine
from game_theory.nash_equilibrium import solve_nash_equilibrium
from agents.optimal_agent import OptimalAgent


def _zone_from_label(label: str) -> GoalZone:
    normalized = label.replace(" ", "_").replace("-", "_").upper()
    try:
        return GoalZone[normalized]
    except KeyError as exc:
        for zone in GoalZone:
            if label == zone.label or label == zone.short_label:
                return zone
        raise ValueError(f"Unknown zone label: {label}") from exc


@dataclass
class MatchController:
    """Track a penalty match and coordinate the AI opponent."""

    role: str = "Shooter"
    total_rounds: int = 5
    seed: int | None = None
    _rng: np.random.Generator = field(init=False, repr=False)
    _engine: PenaltyShootoutEngine = field(init=False, repr=False)
    _ai_shooter: OptimalAgent = field(init=False, repr=False)
    _ai_goalkeeper: OptimalAgent = field(init=False, repr=False)
    _payoff_matrix: PayoffMatrix = field(init=False, repr=False)
    _equilibrium: EquilibriumResult = field(init=False, repr=False)
    _rounds_played: int = field(init=False, default=0)
    _user_score: int = field(init=False, default=0)
    _ai_score: int = field(init=False, default=0)
    _finished: bool = field(init=False, default=False)
    _winner: str | None = field(init=False, default=None)
    _last_outcome: TurnOutcome | None = field(init=False, default=None)
    _history: list[TurnOutcome] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self._rng = np.random.default_rng(self.seed)
        self._payoff_matrix = build_default_penalty_payoff_matrix()
        self._equilibrium = solve_nash_equilibrium(self._payoff_matrix.values)
        self._engine = PenaltyShootoutEngine(self._payoff_matrix, rng=self._rng)
        self._ai_shooter = OptimalAgent(self._equilibrium.shooter_strategy)
        self._ai_goalkeeper = OptimalAgent(self._equilibrium.goalkeeper_strategy)
        self.reset(self.role)

    @property
    def actions(self) -> tuple[GoalZone, ...]:
        return GoalZone.ordered()

    @property
    def payoff_matrix(self) -> PayoffMatrix:
        return self._payoff_matrix

    @property
    def equilibrium(self) -> EquilibriumResult:
        return self._equilibrium

    @property
    def rounds_played(self) -> int:
        return self._rounds_played

    @property
    def user_score(self) -> int:
        return self._user_score

    @property
    def ai_score(self) -> int:
        return self._ai_score

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def winner(self) -> str | None:
        return self._winner

    @property
    def sudden_death(self) -> bool:
        return self._rounds_played >= self.total_rounds and self._user_score == self._ai_score and not self._finished

    @property
    def last_outcome(self) -> TurnOutcome | None:
        return self._last_outcome

    @property
    def history(self) -> tuple[TurnOutcome, ...]:
        return tuple(self._history)

    def reset(self, role: str | None = None) -> None:
        if role is not None:
            normalized = role.strip().lower()
            if normalized not in {"shooter", "goalkeeper"}:
                raise ValueError("Role must be 'Shooter' or 'Goalkeeper'.")
            self.role = "Shooter" if normalized == "shooter" else "Goalkeeper"
        self._rounds_played = 0
        self._user_score = 0
        self._ai_score = 0
        self._finished = False
        self._winner = None
        self._last_outcome = None
        self._history.clear()

    def _choose_ai_zone(self, is_shooter: bool) -> GoalZone:
        agent = self._ai_shooter if is_shooter else self._ai_goalkeeper
        chosen_label = agent.choose_action(tuple(zone.label for zone in self.actions), self._rng)
        return _zone_from_label(chosen_label)

    def _finalize_match_state(self) -> None:
        if self._rounds_played < self.total_rounds:
            self._winner = None
            self._finished = False
            return

        if self._user_score == self._ai_score:
            self._winner = None
            self._finished = False
            return

        self._winner = "You" if self._user_score > self._ai_score else "AI"
        self._finished = True

    def play_turn(self, user_zone: GoalZone) -> TurnOutcome:
        if self._finished:
            raise RuntimeError("The match is already finished. Start a new match.")

        if self.role == "Shooter":
            shooter_zone = user_zone
            goalkeeper_zone = self._choose_ai_zone(is_shooter=False)
        else:
            shooter_zone = self._choose_ai_zone(is_shooter=True)
            goalkeeper_zone = user_zone

        result = self._engine.resolve_penalty(shooter_zone, goalkeeper_zone)

        if self.role == "Shooter":
            if result.scored:
                self._user_score += 1
            else:
                self._ai_score += 1
        else:
            if result.scored:
                self._ai_score += 1
            else:
                self._user_score += 1

        self._rounds_played += 1
        self._finalize_match_state()

        status_message = (
            "GOAL!" if result.scored else "SAVED!"
        )
        if self.sudden_death:
            status_message = f"{status_message} Sudden death."
        if self._finished and self._winner is not None:
            status_message = f"{status_message} Winner: {self._winner}."
        elif self._finished:
            status_message = f"{status_message} Match tied."

        turn = TurnOutcome(
            user_zone=user_zone,
            ai_zone=goalkeeper_zone if self.role == "Shooter" else shooter_zone,
            scored=result.scored,
            scoring_probability=result.scoring_probability,
            round_number=self._rounds_played,
            user_score=self._user_score,
            ai_score=self._ai_score,
            finished=self._finished,
            winner=self._winner,
            status_message=status_message,
        )
        self._last_outcome = turn
        self._history.append(turn)
        return turn
