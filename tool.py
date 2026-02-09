"""Utility wrapper providing a simple `get_completion` helper for notebooks.

This tries to support both the older `openai` module usage (ChatCompletion)
and the newer `openai.OpenAI` client that exposes `responses.create`.
It reads `OPENAI_API_KEY` from the environment (dotenv is supported).
"""
from typing import Optional
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def _make_fallback(message: str):
    def _fn(*args, **kwargs):
        raise RuntimeError(message)

    return _fn


try:
    import openai

    # Prefer the new official client API when available (openai.OpenAI)
    # Newer `openai` package provides `OpenAI` client and `responses.create`.
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url="https://api.gptsapi.net/v1",
        )

        def get_completion(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 512) -> str:
            """Use the new OpenAI.responses API when possible."""
            r = client.responses.create(model=model, input=prompt)
            return getattr(r, "output_text", str(r))

    except Exception:
        # Fallback for older <1.0 style (rare in modern installs).
        # Some modern installs still expose ChatCompletion symbol but it raises APIRemovedInV1,
        # so we avoid calling ChatCompletion if the package reports >=1.0.0.
        ver = getattr(openai, "__version__", None)
        try:
            ver_tuple = tuple(int(x) for x in ver.split(".")[:2]) if ver else (0, 0)
        except Exception:
            ver_tuple = (0, 0)

        if ver_tuple < (1, 0) and hasattr(openai, "ChatCompletion"):
            openai.api_key = OPENAI_API_KEY
            openai.api_base = "https://api.gptsapi.net/v1"

            def get_completion(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 512) -> str:
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content

        else:
            # No usable client available in this environment
            get_completion = _make_fallback("OpenAI client present but incompatible with ChatCompletion; please use the new OpenAI client or install an older openai package.")

except Exception as e:  # pragma: no cover - environment dependent
    get_completion = _make_fallback("OpenAI client not available: %s" % str(e))


if __name__ == "__main__":
    # quick smoke test when executed directly (no network call if key absent)
    try:
        print(get_completion("Say hello in one sentence."))
    except Exception as ex:
        print("get_completion unavailable:", ex)
