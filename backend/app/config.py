
import os
from pathlib import Path
from dotenv import load_dotenv

# Charge toujours le fichier .env situé dans le dossier backend
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://bibliotech_user:CHANGE_ME@localhost:3306/bibliotech_db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    LOAN_DURATION_DAYS = int(os.getenv("LOAN_DURATION_DAYS", "14"))
    MAX_ACTIVE_LOANS = int(os.getenv("MAX_ACTIVE_LOANS", "5"))
    FINE_PER_DAY = int(os.getenv("FINE_PER_DAY", "500"))
    RESERVATION_HOLD_DAYS = int(os.getenv("RESERVATION_HOLD_DAYS", "2"))
