"""Fixture Commit 10: Add caching (NEW FEATURE - MODERATE QUALITY)"""

COMMIT_MESSAGE = "feat: Add caching layer for search"
AUTHOR = "Backend Team"
AUTHOR_EMAIL = "backend@example.com"

FILES = {
    "app/main.py": '''"""Flask web application with multiple security and style issues."""

import logging
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
from flask_cors import CORS
from app import database, config, utils

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS allows all origins
CORS(app, origins="*")

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'}

# Simple in-memory cache (not thread-safe!)
search_cache = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    logger.info("Index endpoint accessed")
    return jsonify({"message": "Welcome to the API"})


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
    
    # Check cache (not thread-safe - potential race condition)
    if query in search_cache:
        logger.info(f"Cache hit: {query}")
        return jsonify({"results": search_cache[query], "cached": True})
    
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


@app.route("/eval", methods=["POST"])
def evaluate_expression():
    data = request.get_json()
    expression = data.get("expression", "")
    
    try:
        result = eval(expression)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
'''
}
