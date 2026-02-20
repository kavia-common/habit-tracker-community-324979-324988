import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

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


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load and return Settings from environment variables.

    Required env vars (provided via .env by orchestrator):
      - POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT
      - JWT_SECRET_KEY
    Optional:
      - JWT_ALGORITHM (default: HS256)
      - ACCESS_TOKEN_EXP_MINUTES (default: 10080 i.e., 7 days)
      - CORS_ORIGINS (default: "*")
    """
    cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
    cors_origins = ["*"] if cors_origins_raw.strip() == "*" else _split_csv(cors_origins_raw)

    jwt_alg = os.getenv("JWT_ALGORITHM", "HS256")
    exp = int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "10080"))

    jwt_secret = os.getenv("JWT_SECRET_KEY", "")
    # Intentionally do not crash at import-time; raise with a clear message when called.
    if not jwt_secret:
        raise RuntimeError("Missing required env var JWT_SECRET_KEY")

    return Settings(
        postgres_url=os.getenv("POSTGRES_URL", ""),
        postgres_user=os.getenv("POSTGRES_USER", ""),
        postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
        postgres_db=os.getenv("POSTGRES_DB", ""),
        postgres_port=os.getenv("POSTGRES_PORT", ""),
        jwt_secret_key=jwt_secret,
        jwt_algorithm=jwt_alg,
        access_token_exp_minutes=exp,
        cors_origins=cors_origins,
    )
