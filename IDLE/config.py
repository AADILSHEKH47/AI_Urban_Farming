"""
Configuration Module for AI Urban Farming Assistant.
Handles environment variables, API keys, database paths, and app defaults.
"""

import os
from pathlib import Path

# Try loading from .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DB_PATH = str(BASE_DIR / "urban_farming.db")

# Master Admin Configuration
MASTER_ADMIN_EMAIL = os.getenv("MASTER_ADMIN_EMAIL", "admin@urbanfarming.com").strip().lower()

# OAuth Configuration (Google & Facebook)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501").strip()

FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID", "").strip()
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET", "").strip()
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8501").strip()

# API Keys (Loaded safely from environment variables or Streamlit secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

# Default Weather Location
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Urban Balcony Garden")
DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "28.6139"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "77.2090"))

# Gemini Model
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

# App Version & Title
APP_TITLE = "AI Urban Farming Assistant 🌱"
APP_SUBTITLE = "Smart Plant Pathology, Care Scheduling & Micro-Climate Irrigation"

