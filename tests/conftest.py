"""Test configuration and fixtures."""

import os
import pytest
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


@pytest.fixture
def github_token() -> str:
    """Get GitHub token from environment.
    
    For integration tests, set GITHUB_TOKEN in .env file.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN not set - skipping integration test")
    return token


@pytest.fixture
def test_repo() -> str:
    """Test repository for integration tests.
    
    Format: "owner/repo"
    Set TEST_REPO in .env or use default test repo.
    """
    return os.getenv("TEST_REPO", "RostislavDublin/test-code-review")


@pytest.fixture
def test_pr_number() -> int:
    """Test PR number for integration tests.
    
    Set TEST_PR_NUMBER in .env or use default.
    """
    return int(os.getenv("TEST_PR_NUMBER", "1"))
