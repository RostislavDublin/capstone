"""Test repository fixture manager for Quality Guardian.

Provides reusable fixture for creating/validating/resetting test GitHub repository.
Used by both demos and integration tests.

Usage:
    from tests.fixtures.test_repo_fixture import ensure_test_repo, get_test_repo_name
    
    # In demo or test:
    repo_name = ensure_test_repo()  # Auto-creates if needed
    # ... use repo_name ...
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from github import Auth, Github
from github.GithubException import UnknownObjectException

logger = logging.getLogger(__name__)

# Load environment once
_env_file = Path(__file__).parent.parent.parent / ".env.dev"
if _env_file.exists():
    load_dotenv(_env_file)

# Constants
TEST_REPO_NAME = os.getenv("TEST_REPO_NAME", "quality-guardian-test-fixture")
TEST_REPO_OWNER = "RostislavDublin"
TEST_REPO_FULL = f"{TEST_REPO_OWNER}/{TEST_REPO_NAME}"
MIN_COMMITS = 5
FIXTURE_PATH = Path(__file__).parent / "test-app"


class TestRepoFixture:
    """Manages test repository lifecycle for demos and tests."""

    def __init__(self, github_token: Optional[str] = None):
        """Initialize fixture with GitHub token."""
        token = github_token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN required in environment or parameter")
        
        auth = Auth.Token(token)
        self.client = Github(auth=auth)
        self.user = self.client.get_user()

    def exists(self) -> bool:
        """Check if test repo exists."""
        try:
            self.client.get_repo(TEST_REPO_FULL)
            return True
        except UnknownObjectException:
            return False

    def get_commit_count(self) -> int:
        """Get number of commits in repo."""
        try:
            repo = self.client.get_repo(TEST_REPO_FULL)
            return repo.get_commits().totalCount
        except Exception:
            return 0

    def is_valid(self) -> bool:
        """Check if repo exists and has sufficient commits."""
        return self.exists() and self.get_commit_count() >= MIN_COMMITS

    def create(self) -> str:
        """Create new test repository.
        
        Returns:
            Repository full name (owner/repo)
        """
        logger.info(f"Creating test repository: {TEST_REPO_NAME}")
        
        repo = self.user.create_repo(
            name=TEST_REPO_NAME,
            description="Test repository for Quality Guardian agent demos and tests",
            private=False,
            auto_init=True,
        )
        
        logger.info(f"✅ Created: {repo.html_url}")
        return TEST_REPO_FULL

    def delete(self) -> None:
        """Delete test repository."""
        logger.info(f"Deleting test repository: {TEST_REPO_NAME}")
        
        try:
            repo = self.client.get_repo(TEST_REPO_FULL)
            repo.delete()
            logger.info("✅ Repository deleted")
        except UnknownObjectException:
            logger.warning("Repository already deleted")

    def populate(self) -> None:
        """Populate repo with test commits from fixture.
        
        Creates 5 controlled commits with test-app code.
        """
        logger.info("Populating repository with test commits...")
        
        if not FIXTURE_PATH.exists():
            raise FileNotFoundError(f"Fixture not found: {FIXTURE_PATH}")
        
        repo = self.client.get_repo(TEST_REPO_FULL)
        
        # Commit 1: Initial structure
        logger.info("  1/5: Initial project structure")
        self._commit_files(repo, [
            ("README.md", FIXTURE_PATH / "README.md"),
            ("requirements.txt", FIXTURE_PATH / "requirements.txt"),
            (".gitignore", FIXTURE_PATH / ".gitignore"),
        ], "Initial commit: project structure")
        
        # Commit 2: Add app module
        logger.info("  2/5: Add application code")
        self._commit_files(repo, [
            ("app/__init__.py", FIXTURE_PATH / "app/__init__.py"),
            ("app/main.py", FIXTURE_PATH / "app/main.py"),
            ("app/config.py", FIXTURE_PATH / "app/config.py"),
        ], "feat: Add main application module")
        
        # Commit 3: Add database (with intentional security issues)
        logger.info("  3/5: Add database module")
        self._commit_files(repo, [
            ("app/database.py", FIXTURE_PATH / "app/database.py"),
        ], "feat: Add database connection")
        
        # Commit 4: Add utilities
        logger.info("  4/5: Add utility functions")
        self._commit_files(repo, [
            ("app/utils.py", FIXTURE_PATH / "app/utils.py"),
        ], "feat: Add utility helpers")
        
        # Commit 5: Add tests
        logger.info("  5/5: Add test suite")
        self._commit_files(repo, [
            ("tests/test_app.py", FIXTURE_PATH / "tests/test_app.py"),
        ], "test: Add initial test suite")
        
        logger.info(f"✅ Created {MIN_COMMITS} commits")

    def _commit_files(self, repo, files: list, message: str) -> None:
        """Commit multiple files to repo."""
        for github_path, local_path in files:
            if not local_path.exists():
                logger.warning(f"File not found: {local_path}, skipping")
                continue
            
            content = local_path.read_text()
            
            try:
                # Try to get existing file
                existing = repo.get_contents(github_path)
                repo.update_file(
                    github_path,
                    message,
                    content,
                    existing.sha,
                )
            except UnknownObjectException:
                # File doesn't exist, create it
                repo.create_file(
                    github_path,
                    message,
                    content,
                )

    def reset(self) -> str:
        """Reset repo to clean state (delete + recreate).
        
        Returns:
            Repository full name (owner/repo)
        """
        logger.info("Resetting test repository to clean state...")
        
        if self.exists():
            self.delete()
        
        self.create()
        self.populate()
        
        logger.info("✅ Repository reset complete")
        return TEST_REPO_FULL

    def ensure(self) -> str:
        """Ensure test repo exists and is valid. Create/reset if needed.
        
        This is the main entry point for demos and tests.
        
        Returns:
            Repository full name (owner/repo)
        """
        if self.is_valid():
            logger.info(f"✅ Test repository ready: {TEST_REPO_FULL}")
            return TEST_REPO_FULL
        
        if self.exists():
            logger.warning("Test repository exists but invalid (insufficient commits)")
            self.delete()
        
        logger.info("Creating test repository...")
        self.create()
        self.populate()
        
        return TEST_REPO_FULL


# Convenience functions for easy import
_fixture_instance: Optional[TestRepoFixture] = None


def get_fixture() -> TestRepoFixture:
    """Get or create fixture instance (singleton)."""
    global _fixture_instance
    if _fixture_instance is None:
        _fixture_instance = TestRepoFixture()
    return _fixture_instance


def ensure_test_repo() -> str:
    """Ensure test repo exists and is valid. Create if needed.
    
    Returns:
        Repository full name (owner/repo)
    """
    return get_fixture().ensure()


def get_test_repo_name() -> str:
    """Get test repository full name without checking existence.
    
    Returns:
        Repository full name (owner/repo)
    """
    return TEST_REPO_FULL


def reset_test_repo() -> str:
    """Reset test repo to clean state (delete + recreate).
    
    Returns:
        Repository full name (owner/repo)
    """
    return get_fixture().reset()


def delete_test_repo() -> None:
    """Delete test repository."""
    get_fixture().delete()


def add_test_commits(count: int = 1) -> int:
    """Add new commits to test repository for sync testing.
    
    Creates simple file modifications and commits them to demonstrate
    the sync functionality detecting new commits.
    
    Args:
        count: Number of commits to add (default: 1)
    
    Returns:
        Number of commits successfully added
    """
    import tempfile
    import subprocess
    from datetime import datetime
    
    fixture = get_fixture()
    repo = fixture.client.get_repo(TEST_REPO_FULL)
    
    added = 0
    for i in range(count):
        try:
            # Create a simple test file with timestamp
            timestamp = datetime.now().isoformat()
            filename = f"test_sync_{timestamp.replace(':', '-')}.txt"
            content = f"Test commit {i+1} added at {timestamp}\n"
            
            # Create file in repo
            repo.create_file(
                path=filename,
                message=f"test: add sync demo commit {i+1}",
                content=content,
                branch=repo.default_branch
            )
            added += 1
            logger.info(f"Added commit {i+1}/{count}: {filename}")
        except Exception as e:
            logger.warning(f"Failed to add commit {i+1}: {e}")
            break
    
    return added
