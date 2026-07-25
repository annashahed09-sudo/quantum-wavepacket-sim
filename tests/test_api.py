"""Integration tests for the FastAPI application layer.

Covers authentication, project CRUD, simulation execution, and system
status reporting.  Uses an isolated SQLite database that is cleaned up
after each module run.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_quantum_platform.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-ci"

from quantum_platform.main import app  # noqa: E402

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_SIM_PARAMS = {
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
}


def _register_and_login(email: str = "researcher@example.com") -> str:
    client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Research User", "password": "StrongPass123"},
    )
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123"})
    return login.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": "Bearer " + token}


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------


class TestAuth:
    def test_register_and_login(self) -> None:
        token = _register_and_login("alice@example.com")
        assert len(token) > 20

        # Duplicate registration should 409
        r = client.post(
            "/api/auth/register",
            json={"email": "alice@example.com", "full_name": "Alice", "password": "AnotherPass123"},
        )
        assert r.status_code == 409

    def test_login_wrong_password(self) -> None:
        r = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "wrong"})
        assert r.status_code == 401

    def test_login_nonexistent_user(self) -> None:
        r = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "StrongPass123"})
        assert r.status_code == 401

    def test_me_endpoint(self) -> None:
        token = _register_and_login("bob@example.com")
        r = client.get("/api/auth/me", headers=_auth_header(token))
        assert r.status_code == 200
        assert r.json()["email"] == "bob@example.com"

    def test_me_without_token(self) -> None:
        r = client.get("/api/auth/me")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Project CRUD tests
# ---------------------------------------------------------------------------


class TestProjects:
    _token: str = ""
    _project_id: int = -1

    @classmethod
    def setup_class(cls) -> None:
        cls._token = _register_and_login("proj_user@example.com")

    def test_create_project(self) -> None:
        r = client.post(
            "/api/projects",
            headers=_auth_header(self._token),
            json={"name": "Tunneling Study", "description": "Barrier penetration analysis"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Tunneling Study"
        self.__class__._project_id = data["id"]

    def test_list_projects(self) -> None:
        r = client.get("/api/projects", headers=_auth_header(self._token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_update_project(self) -> None:
        r = client.patch(
            f"/api/projects/{self._project_id}",
            headers=_auth_header(self._token),
            json={"description": "Updated description"},
        )
        assert r.status_code == 200
        assert r.json()["description"] == "Updated description"

    def test_delete_project(self) -> None:
        r = client.delete(f"/api/projects/{self._project_id}", headers=_auth_header(self._token))
        assert r.status_code == 200
        assert r.json()["deleted"] is True


# ---------------------------------------------------------------------------
# Full integration flow
# ---------------------------------------------------------------------------


class TestFullFlow:
    """Runs through the auth → project → simulation → dashboard flow."""

    def test_auth_project_and_simulation_flow(self) -> None:
        token = _register_and_login("flow@example.com")
        headers = _auth_header(token)

        # Create project
        create_project = client.post(
            "/api/projects",
            headers=headers,
            json={"name": "Wavepacket Project", "description": "Barrier tunneling study"},
        )
        assert create_project.status_code == 200
        project_id = create_project.json()["id"]

        # List projects
        list_projects = client.get("/api/projects", headers=headers)
        assert list_projects.status_code == 200
        assert len(list_projects.json()) == 1

        # Run simulation
        params = {**BASE_SIM_PARAMS, "project_id": project_id}
        run_sim = client.post("/api/simulations/run", headers=headers, json=params)
        assert run_sim.status_code == 200
        result = run_sim.json()
        assert "run_id" in result
        assert "result" in result
        stats = result["result"]["stats"]
        assert abs(stats["norm_final"] - 1.0) < 0.02

        # List simulations
        runs = client.get("/api/simulations", headers=headers)
        assert runs.status_code == 200
        assert len(runs.json()) == 1

        # Dashboard
        dashboard = client.get("/api/dashboard", headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json()["simulation_count"] >= 1
        assert dashboard.json()["project_count"] >= 1


# ---------------------------------------------------------------------------
# System status test
# ---------------------------------------------------------------------------


class TestSystemStatus:
    def test_system_status(self) -> None:
        r = client.get("/api/system/status")
        assert r.status_code == 200
        data = r.json()
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "gpu_name" in data
        # GPU may be "Unavailable" in CI, but the key must exist
        assert data["gpu_name"] is not None


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def teardown_module() -> None:
    db_file = Path("test_quantum_platform.db")
    if db_file.exists():
        db_file.unlink()
