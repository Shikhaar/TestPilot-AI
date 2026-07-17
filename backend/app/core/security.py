"""
TestPilot AI — Security: JWT Authentication & GitHub OAuth.

Provides:
- JWT access and refresh token creation/validation
- Password hashing via bcrypt
- GitHub webhook signature verification
- GitHub OAuth token exchange
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==============================================================================
# Password Utilities
# ==============================================================================


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password: The plain-text password to hash.

    Returns:
        The bcrypt-hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: The plain-text password.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==============================================================================
# JWT Tokens
# ==============================================================================


def create_access_token(
    subject: str | int,
    data: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The subject (typically user ID) to encode.
        data: Additional claims to include in the token.
        expires_delta: Optional custom expiration delta.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(tz=UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if data:
        payload.update(data)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str | int) -> str:
    """Create a JWT refresh token.

    Args:
        subject: The subject (typically user ID) to encode.

    Returns:
        Encoded JWT refresh token string.
    """
    now = datetime.now(tz=UTC)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload dictionary.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def verify_access_token(token: str) -> dict[str, Any] | None:
    """Verify an access token and return its payload.

    Args:
        token: The JWT access token string.

    Returns:
        The decoded payload or None if invalid.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError as e:
        logger.warning("Invalid access token", error=str(e))
        return None


# ==============================================================================
# GitHub Webhook Verification
# ==============================================================================


def verify_github_webhook_signature(
    payload_body: bytes,
    signature_header: str | None,
) -> bool:
    """Verify the GitHub webhook HMAC-SHA256 signature.

    GitHub signs every webhook payload with the configured webhook secret.
    This function verifies that signature to prevent spoofed webhooks.

    Args:
        payload_body: The raw request body bytes.
        signature_header: The 'X-Hub-Signature-256' header value.

    Returns:
        True if the signature is valid, False otherwise.

    References:
        https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
    """
    if not signature_header:
        logger.warning("GitHub webhook received without signature header")
        return False

    if not signature_header.startswith("sha256="):
        logger.warning("GitHub webhook signature has unexpected format", header=signature_header)
        return False

    secret = settings.github_webhook_secret.encode("utf-8")
    expected_signature = hmac.new(secret, payload_body, hashlib.sha256).hexdigest()
    actual_signature = signature_header[7:]  # Remove "sha256=" prefix

    is_valid = hmac.compare_digest(expected_signature, actual_signature)
    if not is_valid:
        logger.warning("GitHub webhook signature verification failed")

    return is_valid
