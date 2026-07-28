from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'tour_femmes.sqlite3'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    AUTO_CREATE_SCHEMA = env_bool("AUTO_CREATE_SCHEMA", True)
    INLINE_ADMIN_JOBS = env_bool("INLINE_ADMIN_JOBS", False)
    PCS_DATABASE_UPLOAD_MAX_BYTES = int(
        os.getenv("PCS_DATABASE_UPLOAD_MAX_BYTES", str(64 * 1024 * 1024))
    )
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
    PCS_BASE_URL = os.getenv("PCS_BASE_URL", "https://www.procyclingstats.com").rstrip("/")
    PCS_REQUEST_DELAY_SECONDS = float(os.getenv("PCS_REQUEST_DELAY_SECONDS", "4"))
    PCS_MAX_RETRIES = int(os.getenv("PCS_MAX_RETRIES", "2"))
    PCS_429_BACKOFF_SECONDS = float(os.getenv("PCS_429_BACKOFF_SECONDS", "10"))
    PCS_IMAGE_REQUEST_DELAY_SECONDS = float(os.getenv("PCS_IMAGE_REQUEST_DELAY_SECONDS", "3"))
    PCS_PROXY_IMAGES = env_bool("PCS_PROXY_IMAGES", True)
    PCS_USER_AGENT = os.getenv(
        "PCS_USER_AGENT",
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
    )
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Europe/Amsterdam")
