# Code Review Test Fixture

**Purpose:** Template repository with intentionally bad code for testing AI Code Review Orchestration System.

## Overview

This directory contains a Flask web application with **documented code quality issues**. It serves as:
- Repeatable test fixture for E2E testing
- Evaluation dataset for issue detection
- Demo scenario for presentations
- Memory Bank training data

## Deployment

This fixture is deployed programmatically to GitHub:

```bash
# Deploy fixture to GitHub
cd /path/to/capstone
python scripts/deploy_fixture.py

# Creates: RostislavDublin/code-review-test-fixture
# Opens test PRs with documented issues
```

## Project Structure

```
test-fixture/
├── app/
│   ├── __init__.py
│   ├── main.py           # Flask app with security issues
│   ├── database.py       # SQL injection vulnerabilities
│   ├── utils.py          # High complexity functions
│   └── config.py         # Hardcoded secrets
├── tests/
│   └── test_app.py       # Insufficient coverage
├── requirements.txt
└── README.md
```

## Documented Issues

### 🚨 Critical Security (4 issues)

**`app/config.py`**
- Line 5: Hardcoded API key `API_KEY = "sk-1234567890abcdef"`
- Line 6: Hardcoded password `DB_PASSWORD = "admin123"`
- Line 8: Debug mode enabled `DEBUG = True`

**`app/database.py`**
- Lines 15-20: SQL injection via f-string `f"SELECT * FROM users WHERE id = {user_id}"`

**`app/main.py`**
- Line 35: Unvalidated user input passed to eval()
- Line 12: CORS with wildcard `CORS(app, origins="*")`

### ⚠️ High Complexity (3 issues)

**`app/utils.py`**
- Function `process_data()` (lines 25-80):
  - Cyclomatic complexity: 18 (threshold: 10)
  - Nested conditionals: 5 levels deep
  - Function length: 120 lines
  - Multiple responsibilities

### 💡 Style & Maintainability (8 issues)

**All files:**
- Mixed naming conventions (camelCase + snake_case)
- Missing docstrings
- No type hints
- Lines > 120 characters
- Unused imports

**`app/database.py`**
- No error handling
- Unclosed database connections
- Global mutable state

**`tests/test_app.py`**
- Only 15% code coverage
- No edge case tests

## Test Scenarios (PRs)

### PR #1: Security Vulnerabilities
- **Branch:** `feature/user-authentication`
- **Changes:** Login endpoint with SQL injection
- **Expected:** 2 critical issues (SQL injection, plaintext password)

### PR #2: Complexity Explosion  
- **Branch:** `feature/data-processing`
- **Changes:** Complex data transformation logic
- **Expected:** 3 high issues (complexity > 15, deep nesting, duplicates)

### PR #3: Style Violations
- **Branch:** `feature/api-refactor`
- **Changes:** API refactor with inconsistent style
- **Expected:** 5 medium issues (naming, formatting, docs)

### PR #4: Clean Code (Control)
- **Branch:** `feature/logging`
- **Changes:** Proper logging implementation
- **Expected:** 0 issues (validates false positive rate)

## Reset Instructions

```bash
# Complete reset (deletes remote repo, recreates)
python scripts/reset_fixture.py

# Recreate PRs only
python scripts/create_test_prs.py --reset

# Verify fixture state
python scripts/verify_fixture.py
```

## Usage in Evalsets

```json
{
  "test_cases": [
    {
      "pr_url": "https://github.com/RostislavDublin/code-review-test-fixture/pull/1",
      "expected_issues": ["sql_injection", "hardcoded_credentials"],
      "min_critical": 2,
      "max_false_positives": 0
    }
  ]
}
```

## Maintenance Notes

- **Never merge PRs** - they stay open permanently
- **Code stays broken** - this is intentional
- **Update this README** when adding new scenarios
- **Track issue patterns** - what agents catch vs miss

## Configuration

Managed via `/src/capstone/config.py`:

```python
TestFixtureConfig:
    remote_repo: "RostislavDublin/code-review-test-fixture"
    local_path: "./test-fixture"
    auto_deploy: False  # Manual deployment by default
```
