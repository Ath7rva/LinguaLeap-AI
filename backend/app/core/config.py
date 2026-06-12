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

@lru_cache()
def get_settings() -> Settings:
    return Settings()
