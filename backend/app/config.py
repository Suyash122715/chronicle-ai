"""Application configuration settings using pydantic-settings BaseSettings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "Chronicle AI"
    API_V1_STR: str = "/api/v1"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"

    # Database Configuration (SQLAlchemy 2 AsyncPG)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chronicle_ai"

    # JWT Configuration
    JWT_SECRET_KEY: str = "insecure_dev_secret_key_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # TODO: Add JWT_REFRESH_TOKEN_EXPIRE_DAYS when refresh tokens are implemented in Phase 2.3


settings = Settings()
