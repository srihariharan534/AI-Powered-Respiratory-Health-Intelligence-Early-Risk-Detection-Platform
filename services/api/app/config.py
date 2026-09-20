"""
NEXUS Central Application Configuration.
Reads settings from environment variables with sensible development defaults.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    POSTGRES_USER: str = "nexus"
    POSTGRES_PASSWORD: str = "nexus_dev_password"
    POSTGRES_DB: str = "nexus_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = (
        "postgresql+psycopg2://nexus:nexus_dev_password@localhost:5432/nexus_db"
    )

    POSTGRES_TEST_DB: str = "nexus_test"
    TEST_DATABASE_URL: str = (
        "postgresql+psycopg2://nexus:nexus_dev_password@localhost:5432/nexus_test"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
