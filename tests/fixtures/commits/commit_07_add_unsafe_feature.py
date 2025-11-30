"""Fixture Commit 07: Add unsafe file upload (MORE REGRESSION)"""

COMMIT_MESSAGE = "feat: Add file upload endpoint"
AUTHOR = "Junior Dev"
AUTHOR_EMAIL = "junior@example.com"

FILES = {
    "app/main.py": '''"""Flask web application with multiple security and style issues."""

import logging
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from app import database, config, utils

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS allows all origins
CORS(app, origins="*")


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
    # No validation
    query = request.args.get("q", "")
    logger.info(f"Search request: {query}")
    results = database.search_users(query)
    return jsonify({"results": results})


@app.route("/upload", methods=["POST"])
def upload_file():
    # Unsafe file upload - no validation!
    file = request.files.get("file")
    if file:
        filename = file.filename
        # Direct path construction - path traversal vulnerability
        filepath = os.path.join("/tmp/uploads", filename)
        file.save(filepath)
        return jsonify({"message": "File uploaded", "path": filepath})
    return jsonify({"error": "No file"}), 400


@app.route("/eval", methods=["POST"])
def evaluate_expression():
    # eval() on user input - code injection
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
