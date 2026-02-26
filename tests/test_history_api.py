from fastapi.testclient import TestClient

from server.main import create_app


def test_history_endpoints_empty(tmp_path, monkeypatch):
    db_path = tmp_path / "history.db"
    monkeypatch.setenv("HISTORY_DB_PATH", str(db_path))
    monkeypatch.setenv("HISTORY_MAX_RECORDS", "100")

    client = TestClient(create_app())

    res = client.get("/api/text/history")
    assert res.status_code == 200
    assert res.json()["items"] == []

    res = client.get("/api/rag/history")
    assert res.status_code == 200
    assert res.json()["items"] == []

    res = client.get("/api/text/history/not-found")
    assert res.status_code == 404
