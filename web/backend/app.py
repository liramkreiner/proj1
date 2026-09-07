"""FastAPI application for the Tactical Penalty Shootout Simulator (web edition).

Layering
--------
* ``game`` / ``game_theory``  -- all mathematics and game logic (framework-free).
* this module                 -- HTTP transport only: parse JSON, call the core,
                                 shape the response, serve the built front-end.

No numerical computation lives here beyond trivial list/array conversion.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from game.config import (  # noqa: E402
    DEFAULT_MONTE_CARLO_GAMES,
    GRID_COLS,
    GRID_ROWS,
    MAX_MONTE_CARLO_GAMES,
    DEFAULT_ROUNDS_PER_SIDE,
)
from game.match_controller import MatchController  # noqa: E402
from game.models import EquilibriumResult, GoalZone, PayoffMatrix  # noqa: E402
from game.payoff_matrix import build_default_penalty_payoff_matrix  # noqa: E402
from game.simulation import run_penalty_monte_carlo  # noqa: E402
from game_theory.nash_equilibrium import solve_nash_equilibrium  # noqa: E402
from web.backend import schemas  # noqa: E402

app = FastAPI(title="Tactical Penalty Shootout Simulator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: dict[str, MatchController] = {}
FRONTEND_DIST = REPO_ROOT / "web" / "frontend" / "dist"

ZONE_LABELS = tuple(zone.label for zone in GoalZone.ordered())


# --------------------------------------------------------------------------- #
# Domain <-> schema helpers
# --------------------------------------------------------------------------- #
def _payoff_matrix_from_values(values: list[list[float]]) -> PayoffMatrix:
    """Build a validated PayoffMatrix from a raw grid, or raise HTTP 422."""

    try:
        array = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Matrix is not numeric: {exc}") from exc

    if array.ndim != 2 or array.shape != (len(ZONE_LABELS), len(ZONE_LABELS)):
        raise HTTPException(
            status_code=422,
            detail=f"Matrix must be {len(ZONE_LABELS)}x{len(ZONE_LABELS)}; got shape {array.shape}.",
        )
    try:
        return PayoffMatrix(array, ZONE_LABELS, ZONE_LABELS)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _strategy_entries(labels: tuple[str, ...], probabilities: np.ndarray) -> list[schemas.StrategyEntry]:
    return [
        schemas.StrategyEntry(label=label, probability=float(probability))
        for label, probability in zip(labels, probabilities, strict=True)
    ]


def _equilibrium_response(payoff_matrix: PayoffMatrix) -> schemas.EquilibriumResponse:
    equilibrium: EquilibriumResult = solve_nash_equilibrium(
        payoff_matrix.values,
        row_labels=payoff_matrix.row_labels,
        column_labels=payoff_matrix.column_labels,
    )
    analysis = equilibrium.pure_strategy_analysis
    validation = equilibrium.validation

    return schemas.EquilibriumResponse(
        payoff_matrix=schemas.MatrixModel(
            row_labels=list(payoff_matrix.row_labels),
            column_labels=list(payoff_matrix.column_labels),
            values=payoff_matrix.values.tolist(),
        ),
        pure_analysis=schemas.PureAnalysisModel(
            row_minima=analysis.row_minima.tolist(),
            column_maxima=analysis.column_maxima.tolist(),
            maximin=analysis.maximin,
            minimax=analysis.minimax,
            saddle_point=list(analysis.saddle_point) if analysis.saddle_point is not None else None,
            saddle_point_value=analysis.saddle_point_value,
            has_pure_equilibrium=analysis.saddle_point is not None,
        ),
        shooter_strategy=_strategy_entries(
            payoff_matrix.row_labels, equilibrium.shooter_strategy.probabilities
        ),
        goalkeeper_strategy=_strategy_entries(
            payoff_matrix.column_labels, equilibrium.goalkeeper_strategy.probabilities
        ),
        game_value=equilibrium.game_value,
        validation=schemas.ValidationModel(
            valid=validation.valid,
            messages=list(validation.messages),
            expected_payoff=validation.expected_payoff,
            game_value=validation.game_value,
            shooter_security_ok=validation.row_constraints_satisfied,
            keeper_ceiling_ok=validation.column_constraints_satisfied,
            value_consistent=validation.expected_value_matches,
        ),
    )


def _session_state(session_id: str, controller: MatchController) -> schemas.SessionState:
    return schemas.SessionState(
        session_id=session_id,
        role=controller.role,  # type: ignore[arg-type]
        rounds_played=controller.rounds_played,
        total_rounds=controller.total_rounds,
        user_score=controller.user_score,
        ai_score=controller.ai_score,
        finished=controller.finished,
        winner=controller.winner,
        sudden_death=controller.sudden_death,
    )


def _zone_from_text(text: str) -> GoalZone:
    normalized = text.strip().replace(" ", "_").replace("-", "_").upper()
    try:
        return GoalZone[normalized]
    except KeyError:
        for zone in GoalZone:
            if text == zone.label or text == zone.short_label:
                return zone
    raise HTTPException(status_code=422, detail=f"Unknown zone: {text!r}")


# --------------------------------------------------------------------------- #
# API: analysis
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config", response_model=schemas.ConfigResponse)
def get_config() -> schemas.ConfigResponse:
    zones = [
        {
            "key": zone.name,
            "short": zone.short_label,
            "label": zone.label,
            "row": index // GRID_COLS,
            "col": index % GRID_COLS,
        }
        for index, zone in enumerate(GoalZone.ordered())
    ]
    return schemas.ConfigResponse(
        zones=zones,
        grid_rows=GRID_ROWS,
        grid_cols=GRID_COLS,
        default_rounds_per_side=DEFAULT_ROUNDS_PER_SIDE,
        default_monte_carlo_games=DEFAULT_MONTE_CARLO_GAMES,
        max_monte_carlo_games=MAX_MONTE_CARLO_GAMES,
    )


@app.get("/api/equilibrium", response_model=schemas.EquilibriumResponse)
def get_equilibrium() -> schemas.EquilibriumResponse:
    """Full game-theory analysis of the default penalty matrix."""

    return _equilibrium_response(build_default_penalty_payoff_matrix())


@app.post("/api/analyze", response_model=schemas.EquilibriumResponse)
def analyze_matrix(payload: schemas.MatrixPayload) -> schemas.EquilibriumResponse:
    """Experiment mode: recalculate the equilibrium for a user-edited matrix."""

    return _equilibrium_response(_payoff_matrix_from_values(payload.values))


@app.post("/api/simulate", response_model=schemas.SimulateResponse)
def simulate(payload: schemas.SimulateRequest) -> schemas.SimulateResponse:
    """Monte Carlo: both players sample their equilibrium mixed strategies."""

    payoff_matrix = (
        _payoff_matrix_from_values(payload.values)
        if payload.values is not None
        else build_default_penalty_payoff_matrix()
    )
    equilibrium = solve_nash_equilibrium(
        payoff_matrix.values,
        row_labels=payoff_matrix.row_labels,
        column_labels=payoff_matrix.column_labels,
    )
    p = equilibrium.shooter_strategy.probabilities
    q = equilibrium.goalkeeper_strategy.probabilities

    result = run_penalty_monte_carlo(
        payoff_matrix.values,
        p,
        q,
        games=payload.games,
        theoretical_value=equilibrium.game_value,
        seed=payload.seed,
    )

    return schemas.SimulateResponse(
        games=result.games_simulated,
        theoretical_value=result.theoretical_value,
        observed_scoring_rate=result.observed_scoring_rate,
        absolute_error=result.absolute_error,
        shooter=[
            schemas.DistributionComparison(label=label, theoretical=float(t), empirical=float(e))
            for label, t, e in zip(payoff_matrix.row_labels, p, result.shooter_frequencies, strict=True)
        ],
        goalkeeper=[
            schemas.DistributionComparison(label=label, theoretical=float(t), empirical=float(e))
            for label, t, e in zip(payoff_matrix.column_labels, q, result.goalkeeper_frequencies, strict=True)
        ],
        shooter_l1_error=float(result.metadata["shooter_l1_error"]),
        goalkeeper_l1_error=float(result.metadata["goalkeeper_l1_error"]),
    )


# --------------------------------------------------------------------------- #
# API: gameplay sessions
# --------------------------------------------------------------------------- #
@app.post("/api/sessions", response_model=schemas.SessionState)
def start_session(request: schemas.StartSessionRequest) -> schemas.SessionState:
    override = _payoff_matrix_from_values(request.values) if request.values is not None else None
    controller = MatchController(
        role=request.role,
        seed=request.seed,
        total_rounds=request.total_rounds,
        payoff_matrix_override=override,
    )
    session_id = uuid.uuid4().hex
    _sessions[session_id] = controller
    return _session_state(session_id, controller)


def _require_session(session_id: str) -> MatchController:
    controller = _sessions.get(session_id)
    if controller is None:
        raise HTTPException(status_code=404, detail="Session not found. Start a new match.")
    return controller


@app.get("/api/sessions/{session_id}", response_model=schemas.SessionState)
def get_session(session_id: str) -> schemas.SessionState:
    return _session_state(session_id, _require_session(session_id))


@app.post("/api/sessions/{session_id}/reset", response_model=schemas.SessionState)
def reset_session(session_id: str) -> schemas.SessionState:
    controller = _require_session(session_id)
    controller.reset(controller.role)
    return _session_state(session_id, controller)


@app.post("/api/sessions/{session_id}/turn", response_model=schemas.TurnResponse)
def play_turn(session_id: str, request: schemas.TurnRequest) -> schemas.TurnResponse:
    controller = _require_session(session_id)
    if controller.finished:
        raise HTTPException(status_code=409, detail="Match already finished. Reset to play again.")

    zone = _zone_from_text(request.zone)
    turn = controller.play_turn(zone)

    if controller.role == "Shooter":
        shooter_zone, goalkeeper_zone = turn.user_zone, turn.ai_zone
    else:
        shooter_zone, goalkeeper_zone = turn.ai_zone, turn.user_zone

    return schemas.TurnResponse(
        state=_session_state(session_id, controller),
        round_number=turn.round_number,
        shooter_zone=shooter_zone.label,
        goalkeeper_zone=goalkeeper_zone.label,
        user_zone=turn.user_zone.label,
        ai_zone=turn.ai_zone.label,
        scored=turn.scored,
        scoring_probability=turn.scoring_probability,
        status_message=turn.status_message,
        winner=turn.winner,
        finished=turn.finished,
    )


# --------------------------------------------------------------------------- #
# Static front-end (built SPA)
# --------------------------------------------------------------------------- #
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/")
@app.get("/{full_path:path}")
def serve_spa(full_path: str = "") -> FileResponse:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.exists():
        raise HTTPException(
            status_code=503,
            detail="Front-end build missing. Run: npm --prefix web/frontend run build",
        )
    return FileResponse(index_file)
