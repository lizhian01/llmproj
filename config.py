import os
from dotenv import load_dotenv, find_dotenv

def load_env() -> None:
    load_dotenv(find_dotenv())

def must_getenv(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v
