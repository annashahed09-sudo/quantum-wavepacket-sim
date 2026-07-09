import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_quantum_platform.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient

from quantum_platform.main import app


client = TestClient(app)


def _register_and_login() -> str:
    client.post(
        "/api/auth/register",
        json={"email": "researcher@example.com", "full_name": "Research User", "password": "StrongPass123"},
    )
    login = client.post("/api/auth/login", json={"email": "researcher@example.com", "password": "StrongPass123"})
    return login.json()["access_token"]


def test_auth_project_and_simulation_flow():
    token = _register_and_login()
    headers = {"Authorization": "Bearer " + token}

    create_project = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Wavepacket Project", "description": "Barrier tunneling study"},
    )
    assert create_project.status_code == 200

    list_projects = client.get("/api/projects", headers=headers)
    assert list_projects.status_code == 200
    assert len(list_projects.json()) == 1

    run_sim = client.post(
        "/api/simulations/run",
        headers=headers,
        json={
            "name": "Test Run",
            "grid_size": 256,
            "steps": 20,
            "sample_stride": 4,
            "dt": 0.01,
            "x_min": -30,
            "x_max": 30,
            "x0": -10,
            "k0": 4,
            "sigma": 1.1,
            "barrier_height": 1.0,
            "barrier_width": 2.5,
            "barrier_center": 0,
        },
    )
    assert run_sim.status_code == 200

    runs = client.get("/api/simulations", headers=headers)
    assert runs.status_code == 200
    assert len(runs.json()) == 1

    dashboard = client.get("/api/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["simulation_count"] >= 1


def teardown_module():
    db_file = Path("test_quantum_platform.db")
    if db_file.exists():
        db_file.unlink()
