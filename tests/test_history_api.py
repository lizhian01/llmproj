import uuid

from fastapi.testclient import TestClient

from server.main import create_app


def _register(client: TestClient, username: str) -> str:
    res = client.post("/api/auth/register", json={"username": username, "password": "pass1234"})
    assert res.status_code == 200
    return res.json()["token"]


def test_history_endpoints_empty(tmp_path, monkeypatch):
    db_path = tmp_path / "app.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("HISTORY_LIMIT", "100")
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    client = TestClient(create_app())

    res = client.get("/api/text/history")
    assert res.status_code == 401

    res = client.get("/api/rag/history")
    assert res.status_code == 401

    token = _register(client, f"user_{uuid.uuid4().hex[:8]}")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/text/history", headers=headers)
    assert res.status_code == 200
    assert res.json()["items"] == []

    res = client.get("/api/rag/history", headers=headers)
    assert res.status_code == 200
    assert res.json()["items"] == []

    res = client.get("/api/text/history/not-found", headers=headers)
    assert res.status_code == 404
