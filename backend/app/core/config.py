from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Project root (backend/)
BASE_DIR = Path(__file__).resolve().parents[2]

APP_NAME = os.getenv("APP_NAME")
APP_VERSION = os.getenv("APP_VERSION")

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))

UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR")
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR")

TESSERACT_PATH = os.getenv("TESSERACT_PATH")
POPPLER_PATH = os.getenv("POPPLER_PATH")

DATABASE_URL = os.getenv("DATABASE_URL")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
)

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Create required folders automatically
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)