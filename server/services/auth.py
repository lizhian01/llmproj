import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict

from fastapi import HTTPException


PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "210000"))
PBKDF2_SALT_BYTES = 16
HASH_PREFIX = "pbkdf2_sha256"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: bytes, secret: str) -> bytes:
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")
    return secret


def _get_jwt_expires_days() -> int:
    raw = os.getenv("JWT_EXPIRES_DAYS", "7")
    try:
        days = int(raw)
    except ValueError:
        days = 7
    return max(days, 1)


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password is required")
    salt = os.urandom(PBKDF2_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "$".join(
        [
            HASH_PREFIX,
            str(PBKDF2_ITERATIONS),
            base64.b64encode(salt).decode("utf-8"),
            base64.b64encode(dk).decode("utf-8"),
        ]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        prefix, iterations, salt_b64, hash_b64 = stored_hash.split("$")
    except ValueError:
        return False
    if prefix != HASH_PREFIX:
        return False
    try:
        iterations_int = int(iterations)
    except ValueError:
        return False
    salt = base64.b64decode(salt_b64)
    expected = base64.b64decode(hash_b64)
    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations_int,
    )
    return hmac.compare_digest(expected, computed)


def create_access_token(*, user_id: str, username: str) -> str:
    now = int(time.time())
    exp = now + _get_jwt_expires_days() * 24 * 60 * 60
    payload = {
        "sub": user_id,
        "username": username,
        "iat": now,
        "exp": exp,
    }
    header = {"alg": "HS256", "typ": "JWT"}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = _sign(signing_input, _get_jwt_secret())
    sig_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = _sign(signing_input, _get_jwt_secret())
    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        payload_json = _b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")

    return payload
