"""Fixture Commit 13: Add authentication (BIG IMPROVEMENT)"""

COMMIT_MESSAGE = "feat: Add JWT authentication"
AUTHOR = "Security Team"
AUTHOR_EMAIL = "security@example.com"

FILES = {
    "app/main.py": '''"""Flask web application with improved security."""

import logging
import os
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
from flask_cors import CORS
from app import database, config, utils

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS now restricted
CORS(app, origins=["https://example.com", "https://api.example.com"])

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'}

search_cache = {}
metrics = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "errors": 0,
    "auth_failures": 0
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def require_auth(f):
    """Simple JWT auth decorator."""
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            metrics["auth_failures"] += 1
            return jsonify({"error": "Unauthorized"}), 401
        
        # Simplified: just check token exists (real impl would verify JWT)
        jwt_token = token.replace("Bearer ", "")
        if not utils.verify_jwt(jwt_token):
            metrics["auth_failures"] += 1
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@app.before_request
def track_request():
    metrics["total_requests"] += 1
    request.start_time = time.time()


@app.route("/")
def index():
    return jsonify({"message": "Welcome to the API"})


@app.route("/metrics")
@require_auth
def get_metrics():
    # Now requires authentication!
    return jsonify(metrics)


@app.route("/user/<int:user_id>")
@require_auth
def get_user(user_id):
    # Now requires authentication!
    user = database.get_user_by_id(user_id)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404


@app.route("/search")
@require_auth
def search():
    query = request.args.get("q", "")
    
    if not query or len(query) > 100:
        return jsonify({"error": "Invalid search query"}), 400
    
    if query in search_cache:
        metrics["cache_hits"] += 1
        return jsonify({"results": search_cache[query], "cached": True})
    
    metrics["cache_misses"] += 1
    results = database.search_users(query)
    search_cache[query] = results
    return jsonify({"results": results, "cached": False})


@app.route("/upload", methods=["POST"])
@require_auth
def upload_file():
    file = request.files.get("file")
    if file and file.filename:
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400
        
        filename = secure_filename(file.filename)
        upload_dir = Path("/tmp/uploads")
        upload_dir.mkdir(exist_ok=True)
        filepath = upload_dir / filename
        file.save(str(filepath))
        return jsonify({"message": "File uploaded", "filename": filename})
    return jsonify({"error": "No file"}), 400


if __name__ == "__main__":
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
'''
}
