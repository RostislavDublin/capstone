"""Flask web application with multiple security and style issues.

ISSUES:
- CORS misconfiguration
- Unvalidated input to eval()
- Missing authentication
- Unused imports
- Inconsistent naming
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os  # 💡 STYLE: Unused import
import sys  # 💡 STYLE: Unused import
from app import config, database, utils

app = Flask(__name__)

# 🚨 CRITICAL: CORS allows all origins
CORS(app, origins="*")


@app.route("/")
def index():
    return jsonify({"message": "Welcome to the API"})


@app.route("/user/<int:user_id>")
def get_user(user_id):
    """💡 STYLE: Missing docstring, no type hints."""
    # 🚨 CRITICAL: No authentication check!
    user = database.get_user_by_id(user_id)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404


@app.route("/eval", methods=["POST"])
def evaluate_expression():
    """🚨 CRITICAL: eval() on user input - code injection!"""
    data = request.get_json()
    expression = data.get("expression", "")
    
    # DANGEROUS: Direct eval of user input
    try:
        result = eval(expression)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/process", methods=["POST"])
def process_data_endpoint():
    """⚠️ HIGH: No input validation."""
    data = request.get_json()
    options = request.args.to_dict()
    
    # No validation before processing
    result = utils.process_data(data, options)
    return jsonify(result)


@app.route("/search")
def search():
    """🚨 CRITICAL: SQL injection via search parameter."""
    query = request.args.get("q", "")
    # Passes unsanitized input to SQL injection vulnerable function
    results = database.search_users(query)
    return jsonify({"results": results})


# 💡 STYLE: Inconsistent naming (camelCase)
@app.route("/calculate")
def calculateTotal():
    """Function name should be snake_case."""
    items = request.get_json()
    total = utils.calculateTotalPrice(items)
    return jsonify({"total": total})


@app.route("/delete/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """🚨 CRITICAL: No authorization, SQL injection."""
    # No check if user has permission to delete
    database.delete_user(user_id)
    return jsonify({"message": "User deleted"}), 200


if __name__ == "__main__":
    # 🚨 CRITICAL: Debug mode from config (hardcoded True)
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
