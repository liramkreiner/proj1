"""Abstract player agent interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np


class BaseAgent(ABC):
    """Base class for both human and AI agents."""

    @abstractmethod
    def choose_action(self, actions: Sequence[str], rng: np.random.Generator) -> str:
        """Select an action from the provided action labels."""
