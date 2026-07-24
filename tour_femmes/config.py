from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'tour_femmes.sqlite3'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
    PCS_BASE_URL = os.getenv("PCS_BASE_URL", "https://www.procyclingstats.com").rstrip("/")
    PCS_REQUEST_DELAY_SECONDS = float(os.getenv("PCS_REQUEST_DELAY_SECONDS", "4"))
    PCS_MAX_RETRIES = int(os.getenv("PCS_MAX_RETRIES", "2"))
    PCS_429_BACKOFF_SECONDS = float(os.getenv("PCS_429_BACKOFF_SECONDS", "10"))
    PCS_IMAGE_REQUEST_DELAY_SECONDS = float(os.getenv("PCS_IMAGE_REQUEST_DELAY_SECONDS", "3"))
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Europe/Amsterdam")
