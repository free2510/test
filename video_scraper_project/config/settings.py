# -*- coding: utf-8 -*-
"""
Configuration file for Video Scraper & Uploader project.
All API keys, URLs, and settings are stored here.

For security, use environment variables in production:
- Copy this file to .env and add it to .gitignore
- Or use a secrets manager
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# ==================== PATHS ====================
BASE_DIR = Path(__file__).resolve().parent.parent
# Default temp folder - can be overridden by user input or environment variable
DEFAULT_TEMP_FOLDER = os.getenv("TEMP_FOLDER", "./temp_videos")
TEMP_FOLDER = None  # Will be set at runtime if not provided via env var
PROCESSED_FILE = os.getenv("PROCESSED_FILE", "./processed_videos.json")
TOKEN_PATH = os.getenv("TOKEN_PATH", "./token.json")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", "./credentials.json")

# ==================== DOODSTREAM CONFIGURATION ====================
DOODSTREAM_API_KEY = os.getenv("DOODSTREAM_API_KEY", "566462d6434dlvqu6fmesc")
DOODSTREAM_API_BASE_URL = os.getenv("DOODSTREAM_API_BASE_URL", "https://doodapi.co/api")
DOODSTREAM_WATCH_BASE_URL = os.getenv("DOODSTREAM_WATCH_BASE_URL", "https://dsvplay.com/e")
DOODSTREAM_DOWNLOAD_BASE_URL = os.getenv("DOODSTREAM_DOWNLOAD_BASE_URL", "https://dsvplay.com/d")
DOODSTREAM_API_DELAY = int(os.getenv("DOODSTREAM_API_DELAY", "15"))  # Seconds between API calls

# ==================== GOOGLE CONFIGURATION ====================
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1Bpvo9v6san0VsD6Y1vW26UlxYWpWDqWFVbFga-Cczjg")
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# ==================== SOURCE WEBSITE CONFIGURATION ====================
CATEGORY_URL = os.getenv("CATEGORY_URL", "https://larozaa.yachts/category.php?cat=ramadan-2026")
CATEGORY_NAME = os.getenv("CATEGORY_NAME", "رمضان 2026 - مسلسلات")
BASE_URL = os.getenv("BASE_URL", "https://larozaa.yachts")

# ==================== HEADERS ====================
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ==================== PROCESSING SETTINGS ====================
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))
VIDEO_MIN_SIZE = int(os.getenv("VIDEO_MIN_SIZE", "1048576"))  # 1MB in bytes
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))

# ==================== SHEET COLUMNS ====================
SHEET_HEADERS = [
    'Timestamp', 
    'Title', 
    'Video ID', 
    'Watch Link', 
    'Series Name', 
    'Category', 
    'DoodStream Watch', 
    'DoodStream Download', 
    'Status'
]
SHEET_RANGE = "Sheet1!A:I"

# ==================== LOGGING ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
