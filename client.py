from openai import OpenAI
from config import load_env, must_getenv

def get_client() -> OpenAI:
    load_env()
    return OpenAI(api_key=must_getenv("OPENAI_API_KEY"))
