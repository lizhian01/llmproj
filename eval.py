import json
import time
from pathlib import Path
from app.pipeline import process_text

def call_with_retry(text: str, max_retry: int = 5):
    # 固定退避：20~25秒左右（你的报错提示就是 20s）
    delay = 22
    for i in range(max_retry):
        try:
            return process_text(text)
        except Exception as e:
            msg = str(e)
            if "Error code: 429" in msg or "rate_limit" in msg:
                # 自动等待后继续（不需要你手动操作）
                time.sleep(delay)
                continue
            raise  # 其他错误直接抛出
    raise RuntimeError("Too many 429 retries")

def main():
    test_path = Path("data/tests.jsonl")
    lines = test_path.read_text(encoding="utf-8").splitlines()

    total = 0
    ok_json = 0
    hit_topic = 0
    hit_sent = 0
    failed = []

    for line in lines:
        if not line.strip():
            continue
        item = json.loads(line)
        total += 1

        try:
            r = call_with_retry(item["text"])
            ok_json += 1

            if r.get("topic") == item.get("expect_topic"):
                hit_topic += 1
            if r.get("sentiment") == item.get("expect_sentiment"):
                hit_sent += 1

        except Exception as e:
            failed.append({"id": item.get("id"), "error": str(e)})

    print(f"Total: {total}")
    print(f"JSON OK: {ok_json}/{total}")
    print(f"Topic hit: {hit_topic}/{total}")
    print(f"Sentiment hit: {hit_sent}/{total}")

    if failed:
        print("\nFailed cases:")
        for f in failed:
            print(f"- {f['id']}: {f['error']}")

if __name__ == "__main__":
    main()
