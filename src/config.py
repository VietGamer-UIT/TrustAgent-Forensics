"""
TrustAgent.Forensics — Application Configuration

Loads settings from environment variables / .env file using pydantic-settings.
Author: VietGamer-UIT (https://github.com/VietGamer-UIT)
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    app_env: str = Field(default="development", description="Environment: development | staging | production")
    app_debug: bool = Field(default=True, description="Enable debug mode")
    app_host: str = Field(default="0.0.0.0", description="Server host")
    app_port: int = Field(default=8000, description="Server port")
    app_secret_key: str = Field(default="dev-secret-key-change-in-production", description="Secret key")

    # --- Gemini API ---
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Gemini model name (2026)")

    # --- Database ---
    database_url: str = Field(
        default="sqlite+aiosqlite:///./trustagent.db",
        description="Database connection URL (PostgreSQL for production, SQLite for dev)",
    )

    # --- Z3 Engine ---
    z3_timeout_ms: int = Field(default=5000, description="Z3 solver timeout in milliseconds")
    z3_max_retries: int = Field(default=3, description="Maximum self-correction retries")

    # --- LangGraph ---
    langgraph_max_iterations: int = Field(default=10, description="Max graph iterations")
    langgraph_human_approval_threshold: int = Field(
        default=50_000_000,
        description="Amount threshold (VND) requiring human approval",
    )

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
