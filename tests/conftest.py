"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


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
