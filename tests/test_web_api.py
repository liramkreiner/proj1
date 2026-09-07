"""Integration tests for the FastAPI web API."""

from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from game.models import GoalZone
from game.payoff_matrix import build_default_penalty_payoff_matrix
from web.backend.app import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_config_lists_six_zones() -> None:
    payload = client.get("/api/config").json()
    assert len(payload["zones"]) == 6
    assert payload["grid_rows"] * payload["grid_cols"] == 6


def test_equilibrium_endpoint_shape_and_validity() -> None:
    payload = client.get("/api/equilibrium").json()

    assert payload["validation"]["valid"] is True
    assert len(payload["shooter_strategy"]) == 6
    assert len(payload["goalkeeper_strategy"]) == 6
    assert abs(sum(entry["probability"] for entry in payload["shooter_strategy"]) - 1.0) < 1e-6
    assert payload["pure_analysis"]["has_pure_equilibrium"] is False
    assert 0.0 < payload["game_value"] < 1.0


def test_analyze_recomputes_for_edited_matrix() -> None:
    values = build_default_penalty_payoff_matrix().values.copy()
    values[0, 0] = 0.99  # make Top-Left far more forgiving
    response = client.post("/api/analyze", json={"values": values.tolist()})

    assert response.status_code == 200
    body = response.json()
    assert body["validation"]["valid"] is True
    # Shooter should now favour Top-Left more than in the default equilibrium.
    assert body["shooter_strategy"][0]["probability"] > 1 / 6


def test_analyze_rejects_out_of_range_matrix() -> None:
    bad = [[1.5] * 6] + [[0.5] * 6] * 5
    assert client.post("/api/analyze", json={"values": bad}).status_code == 422


def test_analyze_rejects_wrong_shape() -> None:
    assert client.post("/api/analyze", json={"values": [[0.5, 0.5], [0.5, 0.5]]}).status_code == 422


def test_simulate_converges_to_theory() -> None:
    response = client.post("/api/simulate", json={"games": 50_000, "seed": 1})
    assert response.status_code == 200
    body = response.json()

    assert body["games"] == 50_000
    assert body["absolute_error"] < 1e-2
    for entry in body["shooter"]:
        assert abs(entry["theoretical"] - entry["empirical"]) < 5e-2


def test_single_penalty_as_shooter() -> None:
    response = client.post("/api/penalty", json={"role": "Shooter", "zone": "Top Left", "seed": 3})
    assert response.status_code == 200
    body = response.json()

    assert body["shooter_zone"] == "Top Left"
    assert body["goalkeeper_zone"] in {zone.label for zone in GoalZone}
    assert isinstance(body["scored"], bool)
    assert 0.0 <= body["scoring_probability"] <= 1.0
    assert len(body["ai_probabilities"]) == 6
    assert abs(sum(entry["probability"] for entry in body["ai_probabilities"]) - 1.0) < 1e-6


def test_single_penalty_as_keeper_is_deterministic_under_seed() -> None:
    a = client.post("/api/penalty", json={"role": "Goalkeeper", "zone": "Bottom Right", "seed": 11}).json()
    b = client.post("/api/penalty", json={"role": "Goalkeeper", "zone": "Bottom Right", "seed": 11}).json()

    assert a["goalkeeper_zone"] == "Bottom Right"
    assert a == b


def test_single_penalty_rejects_unknown_zone() -> None:
    assert client.post("/api/penalty", json={"role": "Shooter", "zone": "Nowhere"}).status_code == 422


def test_session_lifecycle_and_turn_zones() -> None:
    start = client.post("/api/sessions", json={"role": "Shooter", "seed": 42}).json()
    sid = start["session_id"]

    turn = client.post(f"/api/sessions/{sid}/turn", json={"zone": "Top Left"}).json()
    assert turn["state"]["rounds_played"] == 1
    assert turn["user_zone"] == "Top Left"
    assert turn["shooter_zone"] == "Top Left"
    assert turn["goalkeeper_zone"] in {zone.label for zone in GoalZone}

    reset = client.post(f"/api/sessions/{sid}/reset").json()
    assert reset["rounds_played"] == 0


def test_turn_on_missing_session_is_404() -> None:
    assert client.post("/api/sessions/deadbeef/turn", json={"zone": "Top Left"}).status_code == 404


def test_root_serves_html_or_reports_missing_build() -> None:
    response = client.get("/")
    assert response.status_code in {200, 503}
