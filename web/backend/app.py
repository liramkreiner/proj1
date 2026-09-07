"""FastAPI backend for the web version of Tactical Penalty Shootout Simulator."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Literal

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from game.match_controller import MatchController  # noqa: E402
from game.models import GoalZone  # noqa: E402


class StartSessionRequest(BaseModel):
    role: Literal["Shooter", "Goalkeeper"] = "Shooter"
    seed: int | None = None


class TurnRequest(BaseModel):
    zone: str = Field(..., description="Selected goal zone label.")


class SessionState(BaseModel):
    session_id: str
    role: str
    rounds_played: int
    total_rounds: int
    user_score: int
    ai_score: int
    finished: bool
    winner: str | None
    sudden_death: bool


class TurnResponse(BaseModel):
    state: SessionState
    round_number: int
    user_zone: str
    ai_zone: str
    scored: bool
    scoring_probability: float
    status_message: str
    winner: str | None
    finished: bool


class MatrixResponse(BaseModel):
    row_labels: list[str]
    column_labels: list[str]
    values: list[list[float]]


class EquilibriumResponse(BaseModel):
    payoff_matrix: MatrixResponse
    row_minima: list[float]
    column_maxima: list[float]
    maximin: float
    minimax: float
    saddle_point: list[int] | None
    shooter_strategy: list[float]
    goalkeeper_strategy: list[float]
    game_value: float
    validation_messages: list[str]
    valid: bool


app = FastAPI(title="Tactical Penalty Shootout Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: dict[str, MatchController] = {}
FRONTEND_DIST = REPO_ROOT / "web" / "frontend" / "dist"

if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


def _controller_state(session_id: str, controller: MatchController) -> SessionState:
    return SessionState(
        session_id=session_id,
        role=controller.role,
        rounds_played=controller.rounds_played,
        total_rounds=controller.total_rounds,
        user_score=controller.user_score,
        ai_score=controller.ai_score,
        finished=controller.finished,
        winner=controller.winner,
        sudden_death=controller.sudden_death,
    )


def _zone_from_text(zone: str) -> GoalZone:
    normalized = zone.replace(" ", "_").replace("-", "_").upper()
    try:
        return GoalZone[normalized]
    except KeyError as exc:
        for candidate in GoalZone:
            if zone == candidate.label or zone == candidate.short_label:
                return candidate
        raise HTTPException(status_code=400, detail=f"Unknown zone: {zone}") from exc


def _equilibrium_response(controller: MatchController) -> EquilibriumResponse:
    equilibrium = controller.equilibrium
    matrix = controller.payoff_matrix
    analysis = equilibrium.pure_strategy_analysis

    return EquilibriumResponse(
        payoff_matrix=MatrixResponse(
            row_labels=list(matrix.row_labels),
            column_labels=list(matrix.column_labels),
            values=matrix.values.tolist(),
        ),
        row_minima=analysis.row_minima.tolist(),
        column_maxima=analysis.column_maxima.tolist(),
        maximin=analysis.maximin,
        minimax=analysis.minimax,
        saddle_point=list(analysis.saddle_point) if analysis.saddle_point is not None else None,
        shooter_strategy=equality_list(equilibrium.shooter_strategy.probabilities),
        goalkeeper_strategy=equality_list(equilibrium.goalkeeper_strategy.probabilities),
        game_value=equilibrium.game_value,
        validation_messages=list(equilibrium.validation.messages),
        valid=equilibrium.validation.valid,
    )


def equality_list(values: np.ndarray) -> list[float]:
    return [float(value) for value in values]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/equilibrium", response_model=EquilibriumResponse)
def get_equilibrium() -> EquilibriumResponse:
    controller = MatchController(role="Shooter")
    return _equilibrium_response(controller)


@app.post("/api/sessions", response_model=SessionState)
def start_session(request: StartSessionRequest) -> SessionState:
    controller = MatchController(role=request.role, seed=request.seed)
    session_id = uuid.uuid4().hex
    _sessions[session_id] = controller
    return _controller_state(session_id, controller)


@app.get("/api/sessions/{session_id}", response_model=SessionState)
def get_session(session_id: str) -> SessionState:
    controller = _sessions.get(session_id)
    if controller is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return _controller_state(session_id, controller)


@app.post("/api/sessions/{session_id}/reset", response_model=SessionState)
def reset_session(session_id: str) -> SessionState:
    controller = _sessions.get(session_id)
    if controller is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    controller.reset(controller.role)
    return _controller_state(session_id, controller)


@app.post("/api/sessions/{session_id}/turn", response_model=TurnResponse)
def play_turn(session_id: str, request: TurnRequest) -> TurnResponse:
    controller = _sessions.get(session_id)
    if controller is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    turn = controller.play_turn(_zone_from_text(request.zone))
    return TurnResponse(
        state=_controller_state(session_id, controller),
        round_number=turn.round_number,
        user_zone=turn.user_zone.label,
        ai_zone=turn.ai_zone.label,
        scored=turn.scored,
        scoring_probability=turn.scoring_probability,
        status_message=turn.status_message,
        winner=turn.winner,
        finished=turn.finished,
    )


@app.get("/")
@app.get("/{full_path:path}")
def serve_frontend(full_path: str = "") -> FileResponse:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend build not found. Run the Vite build in web/frontend first.",
        )
    return FileResponse(index_file)
