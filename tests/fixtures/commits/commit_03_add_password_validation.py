"""Fixture Commit 03: Add password validation to auth.py"""

COMMIT_MESSAGE = "feat: Add password strength validation"
AUTHOR = "Test Developer"
AUTHOR_EMAIL = "dev@example.com"

FILES = {
    "app/auth.py": '''"""User authentication module."""

import re


def validate_password(password: str) -> bool:
    """Validate password strength.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains digit
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


def authenticate_user(username, password):
    """Authenticate user with username and password."""
    if not username or not password:
        return False
    
    # Validate password strength
    if not validate_password(password):
        return False
    
    return True
'''
}

FILES_CHANGED = ["app/auth.py"]
ADDITIONS = 17
DELETIONS = 1
