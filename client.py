import os

from openai import OpenAI
from config import load_env, must_getenv

def get_client() -> OpenAI:
    load_env()
    proxy = os.getenv("OPENAI_PROXY")
    if proxy:
        if not os.getenv("HTTP_PROXY"):
            os.environ["HTTP_PROXY"] = proxy
        if not os.getenv("HTTPS_PROXY"):
            os.environ["HTTPS_PROXY"] = proxy

    timeout = os.getenv("OPENAI_TIMEOUT", "60")
    max_retries = os.getenv("OPENAI_MAX_RETRIES", "5")

    kwargs = {
        "api_key": must_getenv("OPENAI_API_KEY"),
        "base_url": "https://api.gptsapi.net/v1",
    }
    try:
        kwargs["timeout"] = float(timeout)
    except ValueError:
        raise RuntimeError("OPENAI_TIMEOUT must be a number (seconds)")
    try:
        kwargs["max_retries"] = int(max_retries)
    except ValueError:
        raise RuntimeError("OPENAI_MAX_RETRIES must be an integer")

    return OpenAI(**kwargs)
