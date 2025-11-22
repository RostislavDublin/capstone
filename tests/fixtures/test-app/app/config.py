"""Application configuration."""

# TODO: Move to environment variables
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"
SECRET_KEY = "super-secret-key-12345"
DEBUG = True

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
