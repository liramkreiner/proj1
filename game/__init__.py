"""Game domain: models, configuration, payoff matrix, engine, simulation."""

from .config import MatchRules
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
    TurnOutcome,
)
from .payoff_matrix import (
    PenaltyProbabilityModel,
    build_default_penalty_payoff_matrix,
    build_payoff_matrix,
    default_penalty_probability_model,
)
from .penalty_engine import (
    PenaltyOutcome,
    PenaltyShootoutEngine,
    ProbabilitySampler,
    validate_probability_distribution,
)
from .simulation import (
    run_penalty_monte_carlo,
    simulate_discrete_distribution,
    simulate_penalties,
    summarize_simulation,
)

__all__ = [
    "EquilibriumResult",
    "EquilibriumValidation",
    "GameResult",
    "GoalZone",
    "MatchOutcome",
    "MatchRules",
    "MatchStatistics",
    "PayoffMatrix",
    "PenaltyOutcome",
    "PenaltyProbabilityModel",
    "PenaltyShootoutEngine",
    "PlayerStrategy",
    "ProbabilitySampler",
    "PureStrategyAnalysis",
    "SimulationResult",
    "TurnOutcome",
    "build_default_penalty_payoff_matrix",
    "build_payoff_matrix",
    "default_penalty_probability_model",
    "run_penalty_monte_carlo",
    "simulate_discrete_distribution",
    "simulate_penalties",
    "summarize_simulation",
    "validate_probability_distribution",
]
