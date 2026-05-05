"""Application configuration using pydantic-settings."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Tushare API token (required)
    tushare_token: str = ""

    # Database URL (SQLite with async driver)
    database_url: str = "sqlite+aiosqlite:///./data/stock.db"

    # CORS allowed origins (Vite dev server)
    cors_origins: list[str] = ["http://localhost:5173"]

    # API host and port
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
