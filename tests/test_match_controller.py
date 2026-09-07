from __future__ import annotations

import numpy as np

from game.match_controller import MatchController
from game.models import GoalZone


def test_match_controller_tracks_scoring_and_history() -> None:
    controller = MatchController(role="Shooter", seed=123)

    outcome = controller.play_turn(GoalZone.TOP_LEFT)

    assert outcome.round_number == 1
    assert outcome.user_zone == GoalZone.TOP_LEFT
    assert controller.rounds_played == 1
    assert len(controller.history) == 1
    assert outcome.user_score + outcome.ai_score == 1


def test_match_controller_role_switch_resets_state() -> None:
    controller = MatchController(role="Shooter", seed=123)
    controller.play_turn(GoalZone.TOP_LEFT)
    controller.reset("Goalkeeper")

    assert controller.role == "Goalkeeper"
    assert controller.rounds_played == 0
    assert controller.user_score == 0
    assert controller.ai_score == 0
    assert controller.history == ()


def test_match_controller_eventually_finishes() -> None:
    controller = MatchController(role="Shooter", seed=7)

    while not controller.finished:
        controller.play_turn(GoalZone.BOTTOM_RIGHT)

    assert controller.rounds_played >= 5
    assert controller.winner in {"You", "AI", None}