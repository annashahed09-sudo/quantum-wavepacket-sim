from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_endpoint():
    response = client.post("/simulation/create", json={"config": {"name": "api-run"}})
    assert response.status_code == 200
    assert "run_id" in response.json()
