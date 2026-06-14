from fastapi import HTTPException, Request

from app.core.config import get_settings
from app.services.cache import increment

settings = get_settings()


def client_key(request: Request, scope: str, user_id: int | None = None) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    identity = str(user_id) if user_id else ip
    return f"rate:{scope}:{identity}"


def enforce_rate_limit(request: Request, scope: str, user_id: int | None = None, limit: int | None = None):
    maximum = limit or (settings.ai_rate_limit_per_minute if scope.startswith("ai") else settings.rate_limit_per_minute)
    if settings.environment != "production":
        maximum = max(maximum, 500)
    if increment(client_key(request, scope, user_id), 60) > maximum:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute and try again.")
