"""Game domain models and payoff matrix helpers."""

from .models import (
    EquilibriumResult,
    EquilibriumValidation,
    GameResult,
    GoalZone,
    MatchOutcome,
    MatchStatistics,
    PayoffMatrix,
    PlayerStrategy,
    PureStrategyAnalysis,
    SimulationResult,
)
from .payoff_matrix import (
    PenaltyProbabilityModel,
    build_default_penalty_payoff_matrix,
    build_payoff_matrix,
    default_penalty_probability_model,
)
from .penalty_engine import PenaltyOutcome, PenaltyShootoutEngine, ProbabilitySampler
from .simulation import simulate_discrete_distribution, simulate_penalties, summarize_simulation

__all__ = [
    "EquilibriumResult",
    "EquilibriumValidation",
    "GameResult",
    "GoalZone",
    "MatchStatistics",
    "PayoffMatrix",
    "PenaltyProbabilityModel",
    "PlayerStrategy",
    "PureStrategyAnalysis",
    "SimulationResult",
    "build_default_penalty_payoff_matrix",
    "build_payoff_matrix",
    "default_penalty_probability_model",
    "MatchOutcome",
    "PenaltyOutcome",
    "PenaltyShootoutEngine",
    "ProbabilitySampler",
    "simulate_discrete_distribution",
    "simulate_penalties",
    "summarize_simulation",
]