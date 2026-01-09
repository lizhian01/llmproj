import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client import get_client
client = get_client()

text = ("　据了解，特勤局招聘需经过多轮面试、详尽的背景审查以及淘汰率极高的测谎，\
        即便以联邦政府的标准来看，这套流程也堪称严苛。更关键的是，现有外勤办公室本身人手紧张，\
        难以支撑如此大规模的招聘工作。")

r1 = client.responses.create(
    model="gpt-4o-mini",
    input=f"请总结这段话：{text}"
)
r2 = client.responses.create(
    model="gpt-4o-mini",
    input=(
        "请总结下面文本。\n"
        "改进要求：1) 用'要点1/2/3'列出；2) 每点不超过15字；3) 不要出现原文照抄。\n\n"
        f"{text}"
    )
)

print("v1:\n", r1.output_text)
print("v2:\n", r2.output_text)
