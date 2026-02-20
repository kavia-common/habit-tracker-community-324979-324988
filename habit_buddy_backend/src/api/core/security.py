from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from src.api.core.config import get_settings


def _hashpw(password: str) -> str:
    """
    Internal helper for hashing passwords.

    We intentionally use bcrypt directly instead of passlib's bcrypt handler because
    passlib 1.7.4 is not compatible with bcrypt>=4 (bcrypt 5 removed __about__),
    which caused /auth/register to raise 500s at runtime.
    """
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def _verifypw(password: str, password_hash: str) -> bool:
    """Internal helper for verifying bcrypt hashes."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        # If the stored hash is malformed or not bcrypt, treat as invalid credentials.
        return False


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return _hashpw(password)


# PUBLIC_INTERFACE
def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return _verifypw(password, password_hash)


# PUBLIC_INTERFACE
def create_access_token(*, subject: str) -> str:
    """Create a signed JWT access token for the given subject (user_id)."""
    s = get_settings()
    if not s.jwt_secret_key:
        raise RuntimeError("Missing required env var JWT_SECRET_KEY")
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=s.access_token_exp_minutes)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, s.jwt_secret_key, algorithm=s.jwt_algorithm)


# PUBLIC_INTERFACE
def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises jwt exceptions on failure."""
    s = get_settings()
    if not s.jwt_secret_key:
        raise RuntimeError("Missing required env var JWT_SECRET_KEY")
    return jwt.decode(token, s.jwt_secret_key, algorithms=[s.jwt_algorithm])
