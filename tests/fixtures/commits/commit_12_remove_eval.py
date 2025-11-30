"""Fixture Commit 12: Remove eval endpoint (CLEANUP - QUALITY UP)"""

COMMIT_MESSAGE = "fix: Remove dangerous eval endpoint"
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

# CORS allows all origins (still needs fixing)
CORS(app, origins="*")

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'}

# Simple in-memory cache and metrics
search_cache = {}
metrics = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "errors": 0
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def track_request():
    metrics["total_requests"] += 1
    request.start_time = time.time()


@app.route("/")
def index():
    logger.info("Index endpoint accessed")
    return jsonify({"message": "Welcome to the API"})


@app.route("/metrics")
def get_metrics():
    # Metrics endpoint (still no auth, but less critical)
    return jsonify(metrics)


@app.route("/user/<int:user_id>")
def get_user(user_id):
    # No authentication check
    user = database.get_user_by_id(user_id)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404


@app.route("/search")
def search():
    query = request.args.get("q", "")
    
    if not query or len(query) > 100:
        return jsonify({"error": "Invalid search query"}), 400
    
    if query in search_cache:
        metrics["cache_hits"] += 1
        logger.info(f"Cache hit: {query}")
        return jsonify({"results": search_cache[query], "cached": True})
    
    metrics["cache_misses"] += 1
    logger.info(f"Cache miss: {query}")
    results = database.search_users(query)
    search_cache[query] = results
    return jsonify({"results": results, "cached": False})


@app.route("/upload", methods=["POST"])
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


# Removed dangerous eval endpoint!


if __name__ == "__main__":
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
'''
}
