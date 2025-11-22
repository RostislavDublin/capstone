"""Fixture Commit 02: Fix SQL injection in database.py"""

COMMIT_MESSAGE = "fix: Prevent SQL injection in user queries"
AUTHOR = "Security Team"
AUTHOR_EMAIL = "security@example.com"

FILES = {
    "app/database.py": '''"""Database operations with SQL injection vulnerabilities."""

import sqlite3
from typing import Optional, Dict, Any

# Global mutable state
_connection: Optional[sqlite3.Connection] = None


def get_connection():
    """Get database connection."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect("app.db")
    return _connection


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID.
    
    SQL injection vulnerability - user input directly interpolated into query.
    """
    conn = get_connection()
    # SQL INJECTION HERE - no parameterization
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor = conn.cursor()
    result = cursor.fetchone()
    # Cursor never closed
    return result


def search_users(username: str) -> list:
    """Search users by username - FIXED."""
    conn = get_connection()
    # Fixed: Use parameterized query
    query = "SELECT * FROM users WHERE username LIKE ?"
    cursor = conn.cursor()
    results = cursor.execute(query, (f"%{username}%",)).fetchall()
    cursor.close()
    return results


def delete_user(user_id):
    """Delete user by ID."""
    conn = get_connection()
    query = f"DELETE FROM users WHERE id = {user_id}"
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
'''
}

FILES_CHANGED = ["app/database.py"]
ADDITIONS = 3
DELETIONS = 2
