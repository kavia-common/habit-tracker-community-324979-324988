from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.config import get_settings


def _build_sqlalchemy_url() -> str:
    """Build a SQLAlchemy-compatible Postgres URL from env settings.

    The database container provides POSTGRES_URL as 'postgresql://localhost:5000/myapp'.
    We combine it with credentials.
    """
    s = get_settings()
    if not s.postgres_url:
        raise RuntimeError("Missing required env var POSTGRES_URL")
    if not s.postgres_user:
        raise RuntimeError("Missing required env var POSTGRES_USER")
    if not s.postgres_password:
        raise RuntimeError("Missing required env var POSTGRES_PASSWORD")

    base = s.postgres_url.replace("postgresql://", "")
    return f"postgresql+psycopg://{s.postgres_user}:{s.postgres_password}@{base}"


ENGINE = create_engine(
    _build_sqlalchemy_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False, class_=Session)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
