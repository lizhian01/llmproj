import uuid

from fastapi.testclient import TestClient

from server.main import create_app


def test_register_login_me(tmp_path, monkeypatch):
    db_path = tmp_path / "app.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    client = TestClient(create_app())

    username = f"user_{uuid.uuid4().hex[:8]}"

    res = client.post("/api/auth/register", json={"username": username, "password": "pass1234"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data

    res = client.post("/api/auth/login", json={"username": username, "password": "pass1234"})
    assert res.status_code == 200
    token = res.json()["token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["username"] == username

    res = client.post("/api/auth/login", json={"username": username, "password": "wrongpass"})
    assert res.status_code == 401
