"""Intentionally insecure configuration with hardcoded secrets.

SECURITY ISSUES (documented for testing):
- Hardcoded API keys
- Hardcoded database password
- Debug mode enabled
"""

# 🚨 CRITICAL: Hardcoded API key
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"
SECRET_KEY = "super-secret-key-12345"
DEBUG = True  # 🚨 CRITICAL: Debug in production

DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "myapp",
    "user": "admin",
    "password": DB_PASSWORD,  # Reusing hardcoded password
}

# More configuration
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}
