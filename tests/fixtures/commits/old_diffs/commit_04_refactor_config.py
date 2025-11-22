"""Fixture Commit 04: Refactor config to use environment variables"""

COMMIT_MESSAGE = "refactor: Move secrets to environment variables"
AUTHOR = "DevOps Team"
AUTHOR_EMAIL = "devops@example.com"

# File: app/config.py - Refactor configuration
DIFF = r'''diff --git a/app/config.py b/app/config.py
--- a/app/config.py
+++ b/app/config.py
@@ -1,24 +1,19 @@
 """Intentionally insecure configuration with hardcoded secrets.

 SECURITY ISSUES (documented for testing):
 - Hardcoded API keys
 - Hardcoded database password
 - Debug mode enabled
 """

-# 🚨 CRITICAL: Hardcoded API key
-API_KEY = "sk-1234567890abcdef"
-DB_PASSWORD = "admin123"
-SECRET_KEY = "super-secret-key-12345"
-DEBUG = True  # 🚨 CRITICAL: Debug in production
+import os
+
+# Improved: Use environment variables
+API_KEY = os.getenv("API_KEY", "")
+DB_PASSWORD = os.getenv("DB_PASSWORD", "")
+SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
+DEBUG = os.getenv("DEBUG", "false").lower() == "true"

 DATABASE_CONFIG = {
     "host": "localhost",
     "port": 5432,
     "database": "myapp",
     "user": "admin",
-    "password": DB_PASSWORD,  # Reusing hardcoded password
+    "password": DB_PASSWORD,
 }

 # More configuration
'''

# Expected changes
FILES_CHANGED = ["app/config.py"]
ADDITIONS = 5
DELETIONS = 4
