"""Pytest configuration and shared fixtures."""

import pytest
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file for all tests
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded test environment from {env_file}")
else:
    print(f"⚠️  No .env found at {env_file}")

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def changeset_fixtures():
    """Import and provide changeset fixtures."""
    from tests.fixtures.changesets import ALL_CHANGESETS
    return ALL_CHANGESETS


@pytest.fixture
def github_token() -> str:
    """Mock GitHub token for testing."""
    return "ghp_test_token_mock_12345"


@pytest.fixture
def sample_pr_data() -> dict:
    """Sample PR data for testing."""
    return {
        "number": 1,
        "title": "Test PR",
        "body": "Test PR description",
        "base_branch": "main",
        "head_branch": "feature/test",
        "author": "test-user",
        "state": "open",
    }


@pytest.fixture
def sample_diff() -> str:
    """Sample git diff for testing."""
    return """diff --git a/app/main.py b/app/main.py
index 1234567..abcdefg 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,5 +1,8 @@
 def process_data(data):
-    result = data * 2
+    # Added validation
+    if not data:
+        return None
+    result = data * 2
     return result
"""
