"""Pydantic request/response models for the web API.

These are pure data-transfer objects.  All mathematics happens in ``game`` /
``game_theory``; this module only shapes the JSON.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["Shooter", "Goalkeeper"]


# --------------------------------------------------------------------------- #
# Shared building blocks
# --------------------------------------------------------------------------- #
class MatrixModel(BaseModel):
    row_labels: list[str]
    column_labels: list[str]
    values: list[list[float]]


class StrategyEntry(BaseModel):
    label: str
    probability: float


class PureAnalysisModel(BaseModel):
    row_minima: list[float]
    column_maxima: list[float]
    maximin: float
    minimax: float
    saddle_point: list[int] | None
    saddle_point_value: float | None
    has_pure_equilibrium: bool


class ValidationModel(BaseModel):
    valid: bool
    messages: list[str]
    expected_payoff: float
    game_value: float
    shooter_security_ok: bool
    keeper_ceiling_ok: bool
    value_consistent: bool


class EquilibriumResponse(BaseModel):
    payoff_matrix: MatrixModel
    pure_analysis: PureAnalysisModel
    shooter_strategy: list[StrategyEntry]
    goalkeeper_strategy: list[StrategyEntry]
    game_value: float
    validation: ValidationModel


# --------------------------------------------------------------------------- #
# Experiment mode
# --------------------------------------------------------------------------- #
class MatrixPayload(BaseModel):
    """A user-edited payoff matrix (Experiment mode)."""

    values: list[list[float]] = Field(..., description="Scoring probabilities, one row per shot zone.")


# --------------------------------------------------------------------------- #
# Simulation mode
# --------------------------------------------------------------------------- #
class SimulateRequest(BaseModel):
    values: list[list[float]] | None = Field(
        default=None, description="Payoff matrix to simulate; omitted => default penalty matrix."
    )
    games: int = Field(default=10_000, ge=1, le=2_000_000)
    seed: int | None = None


class DistributionComparison(BaseModel):
    label: str
    theoretical: float
    empirical: float


class SimulateResponse(BaseModel):
    games: int
    theoretical_value: float
    observed_scoring_rate: float
    absolute_error: float
    shooter: list[DistributionComparison]
    goalkeeper: list[DistributionComparison]
    shooter_l1_error: float
    goalkeeper_l1_error: float


# --------------------------------------------------------------------------- #
# Gameplay sessions
# --------------------------------------------------------------------------- #
class StartSessionRequest(BaseModel):
    role: Role = "Shooter"
    seed: int | None = None
    values: list[list[float]] | None = Field(
        default=None, description="Optional custom payoff matrix; the AI re-solves for it."
    )
    total_rounds: int = Field(default=5, ge=1, le=50)


class SessionState(BaseModel):
    session_id: str
    role: Role
    rounds_played: int
    total_rounds: int
    user_score: int
    ai_score: int
    finished: bool
    winner: str | None
    sudden_death: bool


class TurnRequest(BaseModel):
    zone: str = Field(..., description="Selected goal-zone label, e.g. 'Top Right'.")


class TurnResponse(BaseModel):
    state: SessionState
    round_number: int
    shooter_zone: str
    goalkeeper_zone: str
    user_zone: str
    ai_zone: str
    scored: bool
    scoring_probability: float
    status_message: str
    winner: str | None
    finished: bool


class ConfigResponse(BaseModel):
    zones: list[dict]
    grid_rows: int
    grid_cols: int
    default_rounds_per_side: int
    default_monte_carlo_games: int
    max_monte_carlo_games: int
