from __future__ import annotations

from fastapi.testclient import TestClient

from web.backend.app import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_session_lifecycle() -> None:
    start_response = client.post('/api/sessions', json={'role': 'Shooter', 'seed': 42})
    assert start_response.status_code == 200
    session = start_response.json()
    assert session['role'] == 'Shooter'

    turn_response = client.post(f"/api/sessions/{session['session_id']}/turn", json={'zone': 'Top Left'})
    assert turn_response.status_code == 200
    turn = turn_response.json()
    assert turn['state']['rounds_played'] == 1
    assert turn['user_zone'] == 'Top Left'


def test_equilibrium_endpoint() -> None:
    response = client.get('/api/equilibrium')
    assert response.status_code == 200
    payload = response.json()
    assert payload['valid'] is True
    assert len(payload['shooter_strategy']) == 6


def test_root_serves_frontend_shell() -> None:
    response = client.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']