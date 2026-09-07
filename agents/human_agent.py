"""Human agent adapter for tests and future GUI integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Sequence

import numpy as np

from .base_agent import BaseAgent


class HumanAgent(BaseAgent):
    """Human-controlled agent driven by an injected chooser callback.

    The callback keeps the engine independent from any future GUI layer.
    """

    def __init__(self, chooser: Callable[[Sequence[str]], str]) -> None:
        self._chooser = chooser

    def choose_action(self, actions: Sequence[str], rng: np.random.Generator) -> str:
        del rng
        choice = self._chooser(actions)
        if choice not in actions:
            raise ValueError(f"Human agent chose invalid action: {choice}")
        return choice