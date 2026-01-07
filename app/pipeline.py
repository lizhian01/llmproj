import json
import re
from client import get_client

client = get_client()

def safe_json_loads(text: str) -> dict:
    if text is None:
        raise ValueError("Model output is None")
    s = text.strip()
    if not s:
        raise ValueError("Model output is empty")

    # 去掉 ```json ... ```
    if s.startswith("```"):
        s = s.strip("`").strip()
        if s.lower().startswith("json"):
            s = s[4:].strip()

    try:
        return json.loads(s)
    except Exception:
        pass

    m = re.search(r"(\{.*\}|\[.*\])", s, flags=re.DOTALL)
    if m:
        return json.loads(m.group(1))

    raise ValueError("No valid JSON found")

from app.prompt_loader import load_prompt, render_prompt
# ... 你原来的 safe_json_loads 和 client 保持不变

def process_text(text: str) -> dict:
    tpl = load_prompt("extract_all.json.md")
    prompt = render_prompt(tpl, TEXT=text)

    r = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    obj = safe_json_loads(r.output_text)

    # 兜底（你已有就保留）
    obj.setdefault("summary_short", "")
    obj.setdefault("summary_bullets", [])
    obj.setdefault("topic", "其他")
    obj.setdefault("sentiment", "中性")
    obj.setdefault("keywords", [])
    obj.setdefault("entities", {"time": None, "location": None, "people": [], "orgs": []})
    obj.setdefault("rewrite_formal", "")

    ent = obj["entities"] if isinstance(obj["entities"], dict) else {}
    ent.setdefault("time", None)
    ent.setdefault("location", None)
    ent.setdefault("people", [])
    ent.setdefault("orgs", [])
    obj["entities"] = ent

    return obj

