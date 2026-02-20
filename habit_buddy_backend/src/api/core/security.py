from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from src.api.core.config import get_settings

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return PWD_CONTEXT.hash(password)


# PUBLIC_INTERFACE
def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return PWD_CONTEXT.verify(password, password_hash)


# PUBLIC_INTERFACE
def create_access_token(*, subject: str) -> str:
    """Create a signed JWT access token for the given subject (user_id)."""
    s = get_settings()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=s.access_token_exp_minutes)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, s.jwt_secret_key, algorithm=s.jwt_algorithm)


# PUBLIC_INTERFACE
def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises jwt exceptions on failure."""
    s = get_settings()
    return jwt.decode(token, s.jwt_secret_key, algorithms=[s.jwt_algorithm])
