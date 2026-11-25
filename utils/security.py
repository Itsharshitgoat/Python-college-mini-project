"""Security helpers: token generation, hashing and password storage."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

from config import QR_PAYLOAD_PREFIX, TOKEN_BYTES

PBKDF2_ITERATIONS = 210_000
_PBKDF2_PREFIX = "pbkdf2_sha256"


def generate_token() -> str:
    """Generate a cryptographically secure, URL-safe QR token."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Hash a QR token with SHA-256 before storing it in SQLite."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def make_payload(token: str) -> str:
    """Wrap a token in the versioned EVENTRA QR payload."""
    return f"{QR_PAYLOAD_PREFIX}{token}"


def parse_payload(payload: str | None) -> str | None:
    """Extract and validate the token from a scanned QR payload."""
    if not payload:
        return None
    value = payload.strip()
    if not value.startswith(QR_PAYLOAD_PREFIX):
        return None
    token = value[len(QR_PAYLOAD_PREFIX) :].strip()
    return token if len(token) >= 32 else None


def hash_password(password: str) -> str:
    """Return a salted PBKDF2-HMAC-SHA256 password hash."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"{_PBKDF2_PREFIX}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Verify a plain-text password against a stored PBKDF2 hash."""
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != _PBKDF2_PREFIX:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False
