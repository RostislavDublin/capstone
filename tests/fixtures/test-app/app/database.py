"""Database operations with SQL injection vulnerabilities.

SECURITY ISSUES:
- SQL injection via string formatting
- No input validation
- Unclosed connections
- Global mutable state
"""

import sqlite3
from typing import Optional, Dict, Any

# 💡 MAINTAINABILITY: Global mutable state
_connection: Optional[sqlite3.Connection] = None


def get_connection():
    """Get database connection (never closed properly)."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect("app.db")
    return _connection


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """🚨 CRITICAL: SQL injection vulnerability!
    
    User input directly interpolated into query.
    """
    conn = get_connection()
    # SQL INJECTION HERE - no parameterization
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor = conn.cursor()
    result = cursor.fetchone()
    # ⚠️ HIGH: Cursor never closed
    return result


def search_users(username: str) -> list:
    """🚨 CRITICAL: Another SQL injection point."""
    conn = get_connection()
    # Direct string concatenation in query
    query = "SELECT * FROM users WHERE username LIKE '%" + username + "%'"
    cursor = conn.cursor()
    results = cursor.fetchall()
    return results


def delete_user(user_id):
    """🚨 CRITICAL: SQL injection in DELETE."""
    conn = get_connection()
    query = f"DELETE FROM users WHERE id = {user_id}"
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    # No error handling at all


# ⚠️ HIGH: Function never called, but creates connection leak
def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT
        )
    """)
    conn.commit()
