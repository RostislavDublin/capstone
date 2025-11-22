"""Fixture Commit 05: Add input validation to API"""

COMMIT_MESSAGE = "feat: Add request validation middleware"
AUTHOR = "Test Developer"
AUTHOR_EMAIL = "dev@example.com"

# File: app/main.py - Add input validation
DIFF = r'''diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -34,6 +34,12 @@ def get_user(user_id):
 @app.route("/search")
 def search():
     # CRITICAL: SQL injection via search parameter
+    # Add input validation
+    query = request.args.get("q", "")
+
+    if not query or len(query) > 100:
+        return jsonify({"error": "Invalid search query"}), 400
+
     logger.info(f"Search request: {request.args.get('q', '')}")
-    query = request.args.get("q", "")
     results = database.search_users(query)
     return jsonify({"results": results})
'''

# Expected changes
FILES_CHANGED = ["app/main.py"]
ADDITIONS = 6
DELETIONS = 1
