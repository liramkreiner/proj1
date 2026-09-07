"""Agent that samples from an optimal mixed strategy."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from game.models import PlayerStrategy

from .base_agent import BaseAgent


class OptimalAgent(BaseAgent):
    """AI agent that samples from a probability distribution.

    The strategy is not converted into a deterministic rule; randomness is the
    mechanism by which the equilibrium behavior emerges.
    """

    def __init__(self, strategy: PlayerStrategy) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> PlayerStrategy:
        return self._strategy

    def choose_action(self, actions: Sequence[str], rng: np.random.Generator) -> str:
        if len(actions) != self._strategy.probabilities.size:
            raise ValueError("Action labels and strategy probabilities must have the same length.")
        index = int(rng.choice(len(actions), p=self._strategy.probabilities))
        return actions[index]