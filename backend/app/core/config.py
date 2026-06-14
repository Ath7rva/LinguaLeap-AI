from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 10080  # 7 days
    database_url: str = "sqlite:///./lingualeap.db"
    algorithm: str = "HS256"
    frontend_url: str = "http://localhost:5173"
    seed_demo_data: bool = False
    researcher_access_code: str = ""
    refresh_token_expire_days: int = 30
    redis_url: str = ""
    sentry_dsn: str = ""
    email_delivery_mode: str = "console"
    resend_api_key: str = ""
    email_from: str = "LinguaLeap AI <onboarding@resend.dev>"
    rate_limit_per_minute: int = 60
    ai_rate_limit_per_minute: int = 12
    max_audio_bytes: int = 8 * 1024 * 1024
    groq_input_cost_per_million: float = 0.0
    groq_output_cost_per_million: float = 0.0
    environment: str = "development"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
