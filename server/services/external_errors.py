from fastapi import HTTPException
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError


def raise_external_error(exc: Exception, *, action: str) -> None:
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, RateLimitError):
        raise HTTPException(status_code=429, detail=f"{action} failed: upstream rate limit")
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        raise HTTPException(status_code=503, detail=f"{action} failed: upstream unavailable")
    if isinstance(exc, APIError):
        raise HTTPException(status_code=502, detail=f"{action} failed: upstream API error")
    raise HTTPException(status_code=500, detail=f"{action} failed: internal error")
