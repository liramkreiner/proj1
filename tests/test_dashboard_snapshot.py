from __future__ import annotations

from game.match_controller import MatchController


def test_controller_exposes_equilibrium_snapshot() -> None:
    controller = MatchController(role="Shooter", seed=1)

    equilibrium = controller.equilibrium

    assert controller.payoff_matrix.values.shape == (6, 6)
    assert equilibrium.validation.valid
    assert len(equilibrium.shooter_strategy.probabilities) == 6
    assert len(equilibrium.goalkeeper_strategy.probabilities) == 6