from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Project root (backend/)
BASE_DIR = Path(__file__).resolve().parents[2]

APP_NAME = os.getenv(
    "APP_NAME",
    "AI Bill of Lading Extractor"
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0"
)

HOST = os.getenv(
    "HOST",
    "0.0.0.0"
)

PORT = int(
    os.getenv("PORT", "8000")
)

UPLOAD_DIR = BASE_DIR / os.getenv(
    "UPLOAD_DIR",
    "uploads"
)

OUTPUT_DIR = BASE_DIR / os.getenv(
    "OUTPUT_DIR",
    "output"
)

LOG_DIR = BASE_DIR / os.getenv(
    "LOG_DIR",
    "logs"
)

# OCR configuration
TESSERACT_PATH = os.getenv(
    "TESSERACT_PATH",
    ""
)

POPPLER_PATH = os.getenv(
    "POPPLER_PATH",
    ""
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///bl_extractor.db"
)

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key"
)

ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "30"
    )
)

# Gemini API Key
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

# Create required folders automatically
UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)