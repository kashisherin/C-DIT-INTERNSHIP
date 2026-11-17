
import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

COOKIE_NAME = "official_session"

SESSION_DURATION_SECONDS = 8 * 60 * 60


def get_auth_settings():
    """Load and validate official authentication settings."""

    username = os.getenv("OFFICIAL_USERNAME", "").strip()
    password = os.getenv("OFFICIAL_PASSWORD", "")
    secret = os.getenv("OFFICIAL_SESSION_SECRET", "")

    if not username or not password or not secret:
        raise RuntimeError(
            "Official authentication settings are missing from .env."
        )

    if len(secret) < 32:
        raise RuntimeError(
            "OFFICIAL_SESSION_SECRET must contain at least 32 characters."
        )

    return username, password, secret


# ============================================================
# 2. VERIFY LOGIN CREDENTIALS
# ============================================================

def verify_credentials(username: str, password: str) -> bool:
    """Verify the supplied official login credentials."""

    expected_username, expected_password, _secret = (
        get_auth_settings()
    )

    username_valid = hmac.compare_digest(
        username.encode("utf-8"),
        expected_username.encode("utf-8")
    )

    password_valid = hmac.compare_digest(
        password.encode("utf-8"),
        expected_password.encode("utf-8")
    )

    return username_valid and password_valid


# ============================================================
# 3. SESSION TOKEN UTILITIES
# ============================================================

def encode_base64(data: bytes) -> str:
    """URL-safe Base64 without padding."""

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def decode_base64(value: str) -> bytes:
    """Decode URL-safe Base64 with restored padding."""

    padding = "=" * (-len(value) % 4)

    return base64.urlsafe_b64decode(
        value + padding
    )


# ============================================================
# 4. CREATE SIGNED SESSION
# ============================================================

def create_session_token(username: str) -> str:
    """
    Create an HMAC-SHA256 signed session token.

    The token expires after SESSION_DURATION_SECONDS.
    """

    expected_username, _password, secret = get_auth_settings()

    if not hmac.compare_digest(username, expected_username):
        raise ValueError("Invalid official username.")

    payload = {
        "sub": username,
        "exp": int(time.time()) + SESSION_DURATION_SECONDS
    }

    payload_bytes = json.dumps(
        payload,
        separators=(",", ":")
    ).encode("utf-8")

    encoded_payload = encode_base64(payload_bytes)

    signature = hmac.new(
        secret.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256
    ).digest()

    return f"{encoded_payload}.{encode_base64(signature)}"


# ============================================================
# 5. VALIDATE SESSION
# ============================================================

def validate_session_token(token: str | None) -> str | None:
    """
    Validate the session signature and expiration.

    Returns the authenticated username or None.
    """

    if not token:
        return None

    try:
        encoded_payload, supplied_signature = token.split(".", 1)

        expected_username, _password, secret = get_auth_settings()

        expected_signature = hmac.new(
            secret.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256
        ).digest()

        actual_signature = decode_base64(
            supplied_signature
        )

        if not hmac.compare_digest(
            expected_signature,
            actual_signature
        ):
            return None

        payload = json.loads(
            decode_base64(encoded_payload).decode("utf-8")
        )

        username = payload.get("sub")
        expires_at = payload.get("exp")

        if not isinstance(username, str):
            return None

        if not isinstance(expires_at, int):
            return None

        if not hmac.compare_digest(username, expected_username):
            return None

        if expires_at <= int(time.time()):
            return None

        return username

    except (
        ValueError,
        TypeError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        base64.binascii.Error
    ):
        return None
