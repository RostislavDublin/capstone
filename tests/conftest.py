"""Test configuration and fixtures."""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pytest
from dotenv import load_dotenv

# Add src to path for imports in fixtures
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load environment variables from .env
load_dotenv()


@pytest.fixture(scope="session")
def github_token() -> str:
    """Get GitHub token from environment.
    
    For integration tests, set GITHUB_TOKEN in .env file.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN not set - skipping integration test")
    return token


@pytest.fixture(scope="session")
def test_fixture(github_token: str, request) -> Dict[str, Any]:
    """Setup and teardown test repository fixture.
    
    This fixture:
    1. Creates test repository if it doesn't exist
    2. Initializes with test application code
    3. Creates fresh test PRs for this test session
    4. Cleans up test PRs after tests complete
    
    Returns dict with:
        - repo_name: Full repository name (owner/repo)
        - pr_security: PR number for security issues test
        - pr_complexity: PR number for complexity issues test
        - pr_clean: PR number for clean code test
    """
    from tests.fixtures.test_repo_manager import TestRepoManager
    
    manager = TestRepoManager(github_token)
    
    # Setup
    print("\n🚀 Setting up test repository fixture...")
    fixture_data = manager.setup()
    print(f"✅ Test fixture ready: {fixture_data['repo_name']}")
    
    # Provide to tests
    yield fixture_data
    
    # Cleanup
    print("\n🧹 Cleaning up test repository fixture...")
    manager.cleanup()
    print("✅ Cleanup complete")


@pytest.fixture
def test_repo(test_fixture: Dict[str, Any]) -> str:
    """Test repository name for integration tests.
    
    Returns:
        Repository full name (owner/repo)
    """
    return test_fixture["repo_name"]


@pytest.fixture
def test_pr_number(test_fixture: Dict[str, Any]) -> int:
    """Test PR number for integration tests.
    
    Uses PR with security issues by default.
    Tests can override by accessing test_fixture directly.
    
    Returns:
        PR number for security issues test
    """
    return test_fixture["pr_security"]
