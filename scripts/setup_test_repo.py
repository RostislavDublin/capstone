#!/usr/bin/env python3
"""Setup test repository for Quality Guardian demos.

Creates or validates a test GitHub repository with controlled commit history.
Uses tests/fixtures/test-app as source code.

Usage:
    python scripts/setup_test_repo.py --create     # Create new repo
    python scripts/setup_test_repo.py --validate   # Check existing repo
    python scripts/setup_test_repo.py --reset      # Reset to clean state
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from github import Auth, Github

# Load environment
env_file = Path(__file__).parent.parent / ".env.dev"
load_dotenv(env_file)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Constants from environment
TEST_REPO_NAME = os.getenv("TEST_REPO_NAME", "quality-guardian-test-fixture")
TEST_REPO_FULL = f"RostislavDublin/{TEST_REPO_NAME}"
MIN_COMMITS = 5
FIXTURE_PATH = Path(__file__).parent.parent / "tests/fixtures/test-app"


class TestRepoManager:
    """Manages test repository lifecycle."""

    def __init__(self, github_token: str):
        """Initialize with GitHub token."""
        auth = Auth.Token(github_token)
        self.client = Github(auth=auth)
        self.user = self.client.get_user()

    def repo_exists(self) -> bool:
        """Check if test repo exists."""
        try:
            self.client.get_repo(TEST_REPO_FULL)
            return True
        except Exception:
            return False

    def get_commit_count(self) -> int:
        """Get number of commits in repo."""
        try:
            repo = self.client.get_repo(TEST_REPO_FULL)
            commits = list(repo.get_commits())
            return len(commits)
        except Exception as e:
            logger.warning(f"Could not get commit count: {e}")
            return 0

    def create_repo(self) -> None:
        """Create new test repository."""
        logger.info(f"Creating repository: {TEST_REPO_NAME}")
        
        repo = self.user.create_repo(
            name=TEST_REPO_NAME,
            description="Test repository for Quality Guardian agent demos",
            private=False,
            auto_init=True,
        )
        
        logger.info(f"✅ Created: {repo.html_url}")

    def delete_repo(self) -> None:
        """Delete test repository."""
        logger.info(f"Deleting repository: {TEST_REPO_NAME}")
        
        repo = self.client.get_repo(TEST_REPO_FULL)
        repo.delete()
        
        logger.info("✅ Repository deleted")

    def populate_with_commits(self) -> None:
        """Populate repo with test commits from fixture."""
        logger.info("Populating repository with test commits...")
        
        if not FIXTURE_PATH.exists():
            raise FileNotFoundError(f"Fixture not found: {FIXTURE_PATH}")
        
        repo = self.client.get_repo(TEST_REPO_FULL)
        
        # Commit 1: Initial structure
        logger.info("Commit 1/5: Initial project structure")
        self._commit_files(repo, [
            ("README.md", FIXTURE_PATH / "README.md"),
            ("requirements.txt", FIXTURE_PATH / "requirements.txt"),
            (".gitignore", FIXTURE_PATH / ".gitignore"),
        ], "Initial commit: project structure")
        
        # Commit 2: Add app module
        logger.info("Commit 2/5: Add application code")
        self._commit_files(repo, [
            ("app/__init__.py", FIXTURE_PATH / "app/__init__.py"),
            ("app/main.py", FIXTURE_PATH / "app/main.py"),
            ("app/config.py", FIXTURE_PATH / "app/config.py"),
        ], "feat: Add main application module")
        
        # Commit 3: Add database
        logger.info("Commit 3/5: Add database module")
        self._commit_files(repo, [
            ("app/database.py", FIXTURE_PATH / "app/database.py"),
        ], "feat: Add database connection")
        
        # Commit 4: Add utilities
        logger.info("Commit 4/5: Add utility functions")
        self._commit_files(repo, [
            ("app/utils.py", FIXTURE_PATH / "app/utils.py"),
        ], "feat: Add utility helpers")
        
        # Commit 5: Add tests
        logger.info("Commit 5/5: Add test suite")
        self._commit_files(repo, [
            ("tests/test_app.py", FIXTURE_PATH / "tests/test_app.py"),
        ], "test: Add initial test suite")
        
        logger.info(f"✅ Created {MIN_COMMITS} commits with controlled history")

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
            except Exception:
                # File doesn't exist, create it
                repo.create_file(
                    github_path,
                    message,
                    content,
                )

    def validate_repo(self) -> bool:
        """Validate repo has sufficient commits."""
        if not self.repo_exists():
            logger.warning(f"Repository {TEST_REPO_FULL} does not exist")
            return False
        
        commit_count = self.get_commit_count()
        logger.info(f"Repository has {commit_count} commits")
        
        if commit_count < MIN_COMMITS:
            logger.warning(f"Insufficient commits (need {MIN_COMMITS})")
            return False
        
        logger.info("✅ Repository is valid for testing")
        return True

    def reset_repo(self) -> None:
        """Reset repo to clean state."""
        logger.info("Resetting repository to clean state...")
        
        if self.repo_exists():
            self.delete_repo()
        
        self.create_repo()
        self.populate_with_commits()
        
        logger.info("✅ Repository reset complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage test repository for Quality Guardian")
    parser.add_argument("--create", action="store_true", help="Create new repository")
    parser.add_argument("--validate", action="store_true", help="Validate existing repository")
    parser.add_argument("--reset", action="store_true", help="Reset repository to clean state")
    parser.add_argument("--delete", action="store_true", help="Delete repository")
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN not found in environment")
        sys.exit(1)
    
    manager = TestRepoManager(github_token)
    
    try:
        if args.create:
            if manager.repo_exists():
                logger.error(f"Repository {TEST_REPO_FULL} already exists")
                sys.exit(1)
            manager.create_repo()
            manager.populate_with_commits()
        
        elif args.validate:
            if manager.validate_repo():
                sys.exit(0)
            else:
                sys.exit(1)
        
        elif args.reset:
            manager.reset_repo()
        
        elif args.delete:
            if not manager.repo_exists():
                logger.warning(f"Repository {TEST_REPO_FULL} does not exist")
                sys.exit(0)
            manager.delete_repo()
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
