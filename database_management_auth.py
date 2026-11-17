"""Separate authentication for the Official Portal database manager.

Credentials are stored as PBKDF2 hashes in environment variables. The
management session is a short-lived, signed HttpOnly cookie. Every edit or
write/delete request must also supply the separate action password.
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()

COOKIE_NAME = "database_management_session"
SESSION_DURATION_SECONDS = int(
    os.getenv("DB_MANAGEMENT_SESSION_SECONDS", "1800")
)
_PASSWORD_ITERATIONS = 310_000


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    """Return a salted PBKDF2-SHA256 password hash for .env storage."""
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Passwords must contain at least 12 characters.")

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PASSWORD_ITERATIONS,
        dklen=32,
    )
    return f"pbkdf2_sha256${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, encoded_hash: str | None) -> bool:
    if not password or not encoded_hash:
        return False

    try:
        scheme, salt_text, digest_text = encoded_hash.split("$", 2)
        if scheme != "pbkdf2_sha256":
            return False

        salt = _b64decode(salt_text)
        expected = _b64decode(digest_text)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            _PASSWORD_ITERATIONS,
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def is_configured() -> bool:
    return all(
        os.getenv(name)
        for name in (
            "DB_MANAGEMENT_USERNAME",
            "DB_MANAGEMENT_PASSWORD_HASH",
            "DB_MANAGEMENT_ACTION_PASSWORD_HASH",
            "DB_MANAGEMENT_SECRET",
        )
    ) and len(os.getenv("DB_MANAGEMENT_SECRET", "")) >= 32


def verify_login(username: str, password: str) -> bool:
    configured_username = os.getenv("DB_MANAGEMENT_USERNAME", "")
    username_ok = bool(configured_username) and hmac.compare_digest(
        username.strip(), configured_username
    )
    password_ok = verify_password(
        password, os.getenv("DB_MANAGEMENT_PASSWORD_HASH")
    )
    return username_ok and password_ok


def verify_action_password(password: str) -> bool:
    return verify_password(
        password, os.getenv("DB_MANAGEMENT_ACTION_PASSWORD_HASH")
    )


def _secret_key() -> bytes:
    secret = os.getenv("DB_MANAGEMENT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError(
            "DB_MANAGEMENT_SECRET must be configured with at least 32 characters."
        )
    return secret.encode("utf-8")


def create_session_token(username: str) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": username,
        "purpose": "database-management",
        "iat": now,
        "exp": now + SESSION_DURATION_SECONDS,
    }
    body = _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        _secret_key(), body.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{body}.{_b64encode(signature)}"


def validate_session_token(token: str | None) -> str | None:
    if not token:
        return None

    try:
        body, signature_text = token.split(".", 1)
        expected_signature = hmac.new(
            _secret_key(), body.encode("ascii"), hashlib.sha256
        ).digest()
        supplied_signature = _b64decode(signature_text)

        if not hmac.compare_digest(expected_signature, supplied_signature):
            return None

        payload = json.loads(_b64decode(body).decode("utf-8"))
        if payload.get("purpose") != "database-management":
            return None
        if int(payload.get("exp", 0)) <= int(time.time()):
            return None

        username = payload.get("sub")
        return username if isinstance(username, str) and username else None
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, RuntimeError):
        return None


def _setup_credentials() -> None:
    print("Database Management security setup")
    print("Use two different strong passwords (at least 12 characters).")
    username = input("Database Management username: ").strip()
    if not username:
        raise SystemExit("Username cannot be empty.")

    login_password = getpass.getpass("Separate database login password: ")
    action_password = getpass.getpass("Separate edit/delete confirmation password: ")

    if login_password == action_password:
        raise SystemExit("The two passwords must be different.")

    login_hash = hash_password(login_password)
    action_hash = hash_password(action_password)
    secret = secrets.token_urlsafe(48)

    print("\nAdd these lines to your backend .env file:")
    print(f"DB_MANAGEMENT_USERNAME={username}")
    print(f"DB_MANAGEMENT_PASSWORD_HASH={login_hash}")
    print(f"DB_MANAGEMENT_ACTION_PASSWORD_HASH={action_hash}")
    print(f"DB_MANAGEMENT_SECRET={secret}")
    print(f"DB_MANAGEMENT_SESSION_SECONDS={SESSION_DURATION_SECONDS}")
    print("\nDo not share these values or commit .env to Git.")


if __name__ == "__main__":
    _setup_credentials()
