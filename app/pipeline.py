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

def process_text(text: str) -> dict:
    r = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "developer", "content": "你是文本处理系统。只输出纯JSON，不要Markdown，不要解释。必须字段齐全。"},
            {"role": "user", "content": (
                "请对以下文本进行处理，并严格输出JSON，格式必须如下：\n"
                "{\n"
                "  \"summary_short\": \"<=40字一句话摘要\",\n"
                "  \"summary_bullets\": [\"要点1\",\"要点2\",\"要点3\"],\n"
                "  \"topic\": \"科技|教育|生活|财经|娱乐|其他\",\n"
                "  \"sentiment\": \"正面|中性|负面\",\n"
                "  \"keywords\": [\"关键词1\",\"关键词2\",\"关键词3\"],\n"
                "  \"entities\": {\"time\": null, \"location\": null, \"people\": [], \"orgs\": []},\n"
                "  \"rewrite_formal\": \"不新增事实的正式书面改写\"\n"
                "}\n"
                "要求：summary_bullets 必须刚好3条；keywords 刚好3个。\n\n"
                f"文本：{text}"
            )}
        ],
    )

    obj = safe_json_loads(r.output_text)

    # 兜底：保证字段齐全（真实落地必备）
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
