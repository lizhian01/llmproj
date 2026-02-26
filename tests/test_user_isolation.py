import uuid

from fastapi.testclient import TestClient

from server.main import create_app
from server.services.history_store import record_rag_history, record_text_history
from server.services.user_store import upsert_kb_for_upload


def _register(client: TestClient, username: str):
    res = client.post("/api/auth/register", json={"username": username, "password": "pass1234"})
    assert res.status_code == 200
    data = res.json()
    return data["token"], data["user"]


def test_user_isolation(tmp_path, monkeypatch):
    db_path = tmp_path / "app.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    client = TestClient(create_app())

    token_a, user_a = _register(client, f"user_{uuid.uuid4().hex[:8]}")
    token_b, user_b = _register(client, f"user_{uuid.uuid4().hex[:8]}")

    history_a = record_text_history(
        user_id=user_a["id"],
        input_text="hello",
        result={"summary_short": "hi"},
        status="success",
        duration_ms=12,
    )
    history_b = record_text_history(
        user_id=user_b["id"],
        input_text="world",
        result={"summary_short": "wo"},
        status="success",
        duration_ms=18,
    )

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    res = client.get("/api/text/history", headers=headers_a)
    assert res.status_code == 200
    ids_a = [item["id"] for item in res.json()["items"]]
    assert history_a in ids_a
    assert history_b not in ids_a

    res = client.get(f"/api/text/history/{history_b}", headers=headers_a)
    assert res.status_code == 404

    # RAG history isolation
    record_rag_history(
        user_id=user_a["id"],
        kb_id="kb_a",
        question="Q1",
        topk=3,
        threshold=0.3,
        embedding_model="text-embedding-3-small",
        model="gpt-4o-mini",
        result={"answer": "A1", "refused": False, "citations": []},
        status="success",
        duration_ms=10,
    )
    record_rag_history(
        user_id=user_b["id"],
        kb_id="kb_b",
        question="Q2",
        topk=3,
        threshold=0.3,
        embedding_model="text-embedding-3-small",
        model="gpt-4o-mini",
        result={"answer": "A2", "refused": False, "citations": []},
        status="success",
        duration_ms=11,
    )

    res = client.get("/api/rag/history", headers=headers_a)
    assert res.status_code == 200
    assert all(item["kb_id"] != "kb_b" for item in res.json()["items"])

    # KB list isolation
    upsert_kb_for_upload(user_a["id"], "kb_a", "KB A")
    upsert_kb_for_upload(user_b["id"], "kb_b", "KB B")

    res = client.get("/api/kb/list", headers=headers_a)
    assert res.status_code == 200
    kb_ids = [item["kb_id"] for item in res.json()["kbs"]]
    assert "kb_a" in kb_ids
    assert "kb_b" not in kb_ids

    res = client.get("/api/kb/list", headers=headers_b)
    assert res.status_code == 200
    kb_ids = [item["kb_id"] for item in res.json()["kbs"]]
    assert "kb_b" in kb_ids
    assert "kb_a" not in kb_ids
