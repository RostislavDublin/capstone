"""Fixture Commit 04: Refactor config to use environment variables"""

COMMIT_MESSAGE = "refactor: Move secrets to environment variables"
AUTHOR = "DevOps Team"
AUTHOR_EMAIL = "devops@example.com"

FILES = {
    "app/config.py": '''"""Application configuration using environment variables."""

import os

# Use environment variables for sensitive data
API_KEY = os.getenv("API_KEY", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "myapp",
    "user": "admin",
    "password": DB_PASSWORD,
}

# More configuration
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}
'''
}

FILES_CHANGED = ["app/config.py"]
ADDITIONS = 5
DELETIONS = 4
