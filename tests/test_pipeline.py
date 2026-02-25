import json

from app import pipeline


class _FakeResp:
    def __init__(self, output_text: str):
        self.output_text = output_text


class _FakeResponses:
    def create(self, model: str, input: str):
        payload = {
            "summary_short": "ok",
            "summary_bullets": ["a", "b", "c"],
            "topic": "其他",
            "sentiment": "中性",
            "keywords": [],
            "entities": {"time": None, "location": None, "people": [], "orgs": []},
            "rewrite_formal": "ok",
        }
        return _FakeResp(json.dumps(payload, ensure_ascii=False))


class _FakeClient:
    responses = _FakeResponses()


def test_safe_json_loads_supports_markdown_code_fence():
    text = """```json
    {\"a\":1, \"b\":2}
    ```"""
    assert pipeline.safe_json_loads(text) == {"a": 1, "b": 2}


def test_process_text_uses_lazy_client(monkeypatch):
    monkeypatch.setattr(pipeline, "get_client", lambda: _FakeClient())
    monkeypatch.setattr(pipeline, "load_prompt", lambda _: "{TEXT}")
    monkeypatch.setattr(pipeline, "render_prompt", lambda tpl, **kwargs: kwargs["TEXT"])

    out = pipeline.process_text("hello")

    assert out["summary_short"] == "ok"
    assert out["entities"]["people"] == []
