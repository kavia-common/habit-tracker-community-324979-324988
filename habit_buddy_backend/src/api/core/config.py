import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables.

    Note: JWT settings are allowed to be empty in some dev/runtime setups, but
    any endpoint that uses JWT should fail clearly when JWT_SECRET_KEY is not set.
    """

    postgres_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_exp_minutes: int

    cors_origins: list[str]


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _get_cors_origins() -> list[str]:
    """
    Prefer ALLOWED_ORIGINS (present in orchestrator-provided .env) but also
    support CORS_ORIGINS (used in .env.example).
    """
    raw = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS") or "*"
    raw = raw.strip()
    return ["*"] if raw == "*" else _split_csv(raw)


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load and return Settings from environment variables.

    Required for DB connectivity:
      - POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD
    Required for authenticated routes:
      - JWT_SECRET_KEY

    Optional:
      - POSTGRES_DB, POSTGRES_PORT (may be embedded in POSTGRES_URL)
      - JWT_ALGORITHM (default: HS256)
      - ACCESS_TOKEN_EXP_MINUTES (default: 10080 i.e., 7 days)
      - ALLOWED_ORIGINS or CORS_ORIGINS (default: "*")
    """
    jwt_alg = os.getenv("JWT_ALGORITHM", "HS256")
    exp = int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "10080"))

    return Settings(
        postgres_url=os.getenv("POSTGRES_URL", ""),
        postgres_user=os.getenv("POSTGRES_USER", ""),
        postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
        postgres_db=os.getenv("POSTGRES_DB", ""),
        postgres_port=os.getenv("POSTGRES_PORT", ""),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", ""),
        jwt_algorithm=jwt_alg,
        access_token_exp_minutes=exp,
        cors_origins=_get_cors_origins(),
    )
