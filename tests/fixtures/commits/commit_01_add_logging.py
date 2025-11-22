"""Fixture Commit 01: Add logging to Flask app"""

COMMIT_MESSAGE = "feat: Add logging to API endpoints"
AUTHOR = "Test Developer"
AUTHOR_EMAIL = "dev@example.com"

FILES = {
    "app/main.py": '''"""Flask web application with multiple security and style issues."""

import logging
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
    # SQL injection via search parameter
    logger.info(f"Search request: {request.args.get('q', '')}")
    query = request.args.get("q", "")
    results = database.search_users(query)
    return jsonify({"results": results})


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

FILES_CHANGED = ["app/main.py"]
ADDITIONS = 8
DELETIONS = 0
