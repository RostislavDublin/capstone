"""Fixture Commit 03: Add password validation to auth.py"""

COMMIT_MESSAGE = "feat: Add password strength validation"
AUTHOR = "Test Developer"
AUTHOR_EMAIL = "dev@example.com"

# File: app/auth.py - Add password validation
DIFF = r'''diff --git a/app/auth.py b/app/auth.py
--- a/app/auth.py
+++ b/app/auth.py
@@ -1,10 +1,26 @@
 """User authentication module."""

+import re
+
+
+def validate_password(password: str) -> bool:
+    """Validate password strength."""
+    if len(password) < 8:
+        return False
+    if not re.search(r"[A-Z]", password):
+        return False
+    if not re.search(r"[0-9]", password):
+        return False
+    return True
+
+
 def authenticate_user(username, password):
     """Authenticate user with username and password."""
     # Simple authentication logic
     if not username or not password:
         return False
-
-    # TODO: Add password validation
+
+    # Validate password strength
+    if not validate_password(password):
+        return False
+
     return True
'''

# Expected changes
FILES_CHANGED = ["app/auth.py"]
ADDITIONS = 17
DELETIONS = 1
