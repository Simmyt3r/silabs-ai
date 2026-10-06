from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "Silabs AI"


def test_model_status():
    response = client.get("/v1/model")
    assert response.status_code == 200
    assert "model_id" in response.json()
