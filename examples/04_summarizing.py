import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client import get_client
from app.pipeline import process_text


def read_sample(path: str = "data/sample.txt") -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def quick_summary(client, text: str) -> str:
    prompt = f"请用一句不超过40字的话总结下面文本的要点：\n\n{text}"
    r = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )
    return r.output_text


def structured_summary(text: str) -> dict:
    return process_text(text)


def main():
    client = get_client()
    text = read_sample()

    print("--- 快速一句话摘要 ---")
    try:
        one = quick_summary(client, text)
        print(one)
    except Exception as e:
        print("快速摘要失败：", e)

    print("\n--- 结构化摘要（JSON） ---")
    try:
        obj = structured_summary(text)
        import json

        print(json.dumps(obj, ensure_ascii=False, indent=2))
    except Exception as e:
        print("结构化摘要失败：", e)


if __name__ == '__main__':
    main()
