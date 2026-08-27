"""Application configuration loaded from environment variables."""

import os


class Settings:
    """Runtime settings for the showcase API.

    Attributes mirror the .env.example contract; no secrets are required.
    """

    def __init__(self) -> None:
        self.app_port: int = int(os.environ.get("APP_PORT", "8005"))
        self.postgres_host: str = os.environ.get("POSTGRES_HOST", "postgres")
        self.postgres_port: int = int(os.environ.get("POSTGRES_PORT", "5432"))
        self.postgres_user: str = os.environ.get("POSTGRES_USER", "ppaa")
        self.postgres_password: str = os.environ.get("POSTGRES_PASSWORD", "ppaa_local")
        self.postgres_db: str = os.environ.get("POSTGRES_DB", "ppaa_showcase")
        self.redis_host: str = os.environ.get("REDIS_HOST", "redis")
        self.redis_port: int = int(os.environ.get("REDIS_PORT", "6379"))
        self.allowed_origins: list[str] = [
            o.strip()
            for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5174,http://127.0.0.1:5174").split(",")
            if o.strip()
        ]


settings = Settings()
