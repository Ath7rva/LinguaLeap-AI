from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import SessionLocal, run_migrations
from app.api.routes import advanced, auth, platform
from app.core.config import get_settings
from app.services.seed import seed_demo_data
from app.services.observability import RequestContextMiddleware, security_headers

settings = get_settings()

if settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment, traces_sample_rate=0.15)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    run_migrations()
    if settings.seed_demo_data:
        db = SessionLocal()
        try:
            seed_demo_data(db)
        finally:
            db.close()
    yield


app = FastAPI(
    title="LinguaLeap AI",
    description="Intelligent Language Learning Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        return security_headers(await call_next(request))


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router)
app.include_router(platform.router)
app.include_router(advanced.router)

@app.get("/")
def root():
    return {"message": "LinguaLeap AI API", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
