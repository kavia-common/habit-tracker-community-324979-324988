from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import get_settings
from src.api.routers.auth import router as auth_router
from src.api.routers.badges import router as badges_router
from src.api.routers.challenges import router as challenges_router
from src.api.routers.feed import router as feed_router
from src.api.routers.groups import router as groups_router
from src.api.routers.habits import router as habits_router
from src.api.routers.notifications import router as notifications_router
from src.api.schemas import HealthResponse

openapi_tags = [
    {"name": "auth", "description": "User registration/login and profile."},
    {"name": "habits", "description": "Habit CRUD, check-ins, and streaks."},
    {"name": "groups", "description": "Accountability groups and memberships."},
    {"name": "challenges", "description": "Group/community challenges."},
    {"name": "badges", "description": "Badge definitions and user-earned badges."},
    {"name": "notifications", "description": "User notifications."},
    {"name": "feed", "description": "Community feed posts, likes, and comments."},
]


app = FastAPI(
    title="Habit Buddy API",
    description="Backend API for Habit Buddy: social habit tracking with groups, challenges, badges, notifications, and feed.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

settings = None
try:
    settings = get_settings()
except Exception:
    # Allow app to start for health/docs even if env not configured in some dev flows.
    settings = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse, summary="Health check", tags=["auth"])
def health_check() -> HealthResponse:
    """Backend health check endpoint."""
    return HealthResponse(message="Healthy")


app.include_router(auth_router)
app.include_router(habits_router)
app.include_router(groups_router)
app.include_router(challenges_router)
app.include_router(badges_router)
app.include_router(notifications_router)
app.include_router(feed_router)
