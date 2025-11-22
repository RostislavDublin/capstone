"""Fixture Commit 01: Add logging to Flask app"""

COMMIT_MESSAGE = "feat: Add logging to API endpoints"
AUTHOR = "Test Developer"
AUTHOR_EMAIL = "dev@example.com"

# File: app/main.py - Add logging
DIFF = r'''diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,9 +1,14 @@
 """Flask web application with multiple security and style issues."""

+import logging
 from flask import Flask, request, jsonify
 from flask_cors import CORS
 from app import database, config, utils

+# Setup logging
+logging.basicConfig(level=logging.INFO)
+logger = logging.getLogger(__name__)
+
 app = Flask(__name__)

 # CRITICAL: CORS allows all origins
@@ -12,6 +17,7 @@ CORS(app, origins="*")

 @app.route("/")
 def index():
+    logger.info("Index endpoint accessed")
     return jsonify({"message": "Welcome to the API"})


@@ -28,6 +34,7 @@ def get_user(user_id):
 @app.route("/search")
 def search():
     # CRITICAL: SQL injection via search parameter
+    logger.info(f"Search request: {request.args.get('q', '')}")
     query = request.args.get("q", "")
     results = database.search_users(query)
     return jsonify({"results": results})
'''

# Expected changes
FILES_CHANGED = ["app/main.py"]
ADDITIONS = 8
DELETIONS = 0
