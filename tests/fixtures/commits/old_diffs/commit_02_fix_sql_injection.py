"""Fixture Commit 02: Fix SQL injection in database.py"""

COMMIT_MESSAGE = "fix: Prevent SQL injection in user queries"
AUTHOR = "Security Team"
AUTHOR_EMAIL = "security@example.com"

# File: app/database.py - Fix SQL injection
DIFF = r'''diff --git a/app/database.py b/app/database.py
--- a/app/database.py
+++ b/app/database.py
@@ -42,9 +42,10 @@ def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
 def search_users(username: str) -> list:
     """🚨 CRITICAL: Another SQL injection point."""
     conn = get_connection()
-    # Direct string concatenation in query
-    query = "SELECT * FROM users WHERE username LIKE '%" + username + "%'"
+    # Fixed: Use parameterized query
+    query = "SELECT * FROM users WHERE username LIKE ?"
     cursor = conn.cursor()
-    results = cursor.fetchall()
+    results = cursor.execute(query, (f"%{username}%",)).fetchall()
+    cursor.close()
     return results
'''

# Expected changes
FILES_CHANGED = ["app/database.py"]
ADDITIONS = 3
DELETIONS = 2
