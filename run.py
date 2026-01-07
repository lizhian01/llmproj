import json
import sys
from pathlib import Path
from datetime import datetime

from app.pipeline import process_text


def to_markdown_report(input_path: Path, source_text: str, result: dict) -> str:
    """把 result.json 转成一份适合人阅读/截图展示的 Markdown 报告。"""

    # 原文太长会影响展示，这里截断一下（你也可以改成更长）
    preview_len = 800
    preview_text = source_text.strip()
    if len(preview_text) > preview_len:
        preview_text = preview_text[:preview_len] + " ...（略）"

    bullets = result.get("summary_bullets", [])
    keywords = result.get("keywords", [])
    entities = result.get("entities", {}) or {}

    time = entities.get("time", None)
    location = entities.get("location", None)
    people = entities.get("people", [])
    orgs = entities.get("orgs", [])

    md = []
    md.append(f"# 文本处理辅助系统报告\n")
    md.append(f"- 输入文件：`{input_path.as_posix()}`")
    md.append(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    md.append("## 1. 原文（截断预览）")
    md.append("```")
    md.append(preview_text)
    md.append("```\n")

    md.append("## 2. 一句话摘要")
    md.append(result.get("summary_short", "").strip() + "\n")

    md.append("## 3. 要点摘要（3条）")
    for i, b in enumerate(bullets, 1):
        md.append(f"{i}. {b}")
    md.append("")

    md.append("## 4. 分类与情绪")
    md.append(f"- 主题（topic）：**{result.get('topic','')}**")
    md.append(f"- 情绪（sentiment）：**{result.get('sentiment','')}**\n")

    md.append("## 5. 关键词")
    if keywords:
        md.append("- " + "、".join(keywords) + "\n")
    else:
        md.append("- （无）\n")

    md.append("## 6. 实体信息抽取")
    md.append(f"- 时间：{time}")
    md.append(f"- 地点：{location}")
    md.append(f"- 人物：{people}")
    md.append(f"- 组织：{orgs}\n")

    md.append("## 7. 正式书面改写")
    md.append(result.get("rewrite_formal", "").strip() + "\n")

    return "\n".join(md)


def main():
    if len(sys.argv) < 2:
        print("用法：python run.py <input.txt>")
        sys.exit(1)

    p = Path(sys.argv[1])
    text = p.read_text(encoding="utf-8")

    # 调用你的 LLM 文本处理流水线
    result = process_text(text)

    # 1) 输出 JSON
    out_json = p.with_suffix(".result.json")
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2) 输出 Markdown 报告
    out_md = p.with_suffix(".report.md")
    out_md.write_text(to_markdown_report(p, text, result), encoding="utf-8")

    print("已生成：", out_json)
    print("已生成：", out_md)


if __name__ == "__main__":
    main()
