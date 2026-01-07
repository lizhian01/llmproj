from pathlib import Path

def load_prompt(name: str) -> str:
    p = Path("prompts") / name
    return p.read_text(encoding="utf-8")

def render_prompt(tpl: str, **kwargs) -> str:
    out = tpl
    for k, v in kwargs.items():
        out = out.replace("{{" + k + "}}", v)
    return out
