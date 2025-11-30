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
import shutil
import subprocess
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
MIN_COMMITS = 15
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
        
        Creates 15 controlled commits with test-app code.
        """
        logger.info("Populating repository with test commits...")
        
        if not FIXTURE_PATH.exists():
            raise FileNotFoundError(f"Fixture not found: {FIXTURE_PATH}")
        
        repo = self.client.get_repo(TEST_REPO_FULL)
        
        # Commit 1: Initial structure
        logger.info("  1/15: Initial project structure")
        self._commit_files(repo, [
            ("README.md", FIXTURE_PATH / "README.md"),
            ("requirements.txt", FIXTURE_PATH / "requirements.txt"),
            (".gitignore", FIXTURE_PATH / ".gitignore"),
        ], "Initial commit: project structure")
        
        # Commit 2: Add app module
        logger.info("  2/15: Add application code")
        self._commit_files(repo, [
            ("app/__init__.py", FIXTURE_PATH / "app/__init__.py"),
            ("app/main.py", FIXTURE_PATH / "app/main.py"),
            ("app/config.py", FIXTURE_PATH / "app/config.py"),
        ], "feat: Add main application module")
        
        # Commit 3: Add database (with intentional security issues)
        logger.info("  3/15: Add database module")
        self._commit_files(repo, [
            ("app/database.py", FIXTURE_PATH / "app/database.py"),
        ], "feat: Add database connection")
        
        # Commit 4: Add utilities
        logger.info("  4/15: Add utility functions")
        self._commit_files(repo, [
            ("app/utils.py", FIXTURE_PATH / "app/utils.py"),
        ], "feat: Add utility helpers")
        
        # Commit 5: Add tests
        logger.info("  5/15: Add test suite")
        self._commit_files(repo, [
            ("tests/test_app.py", FIXTURE_PATH / "tests/test_app.py"),
        ], "test: Add initial test suite")
        
        # Commit 6: Update README
        logger.info("  6/15: Update documentation")
        self._commit_files(repo, [
            ("README.md", FIXTURE_PATH / "README.md"),
        ], "docs: Update README with usage examples")
        
        # Commit 7: Refactor main
        logger.info("  7/15: Refactor main module")
        self._commit_files(repo, [
            ("app/main.py", FIXTURE_PATH / "app/main.py"),
        ], "refactor: Improve main module structure")
        
        # Commit 8: Update config
        logger.info("  8/15: Update configuration")
        self._commit_files(repo, [
            ("app/config.py", FIXTURE_PATH / "app/config.py"),
        ], "feat: Enhance configuration options")
        
        # Commit 9: Improve database
        logger.info("  9/15: Improve database module")
        self._commit_files(repo, [
            ("app/database.py", FIXTURE_PATH / "app/database.py"),
        ], "fix: Improve database error handling")
        
        # Commit 10: Update utils
        logger.info("  10/15: Update utilities")
        self._commit_files(repo, [
            ("app/utils.py", FIXTURE_PATH / "app/utils.py"),
        ], "feat: Add new utility functions")
        
        # Commit 11: Improve tests
        logger.info("  11/15: Enhance test coverage")
        self._commit_files(repo, [
            ("tests/test_app.py", FIXTURE_PATH / "tests/test_app.py"),
        ], "test: Improve test coverage")
        
        # Commit 12: Code cleanup
        logger.info("  12/15: Code cleanup")
        self._commit_files(repo, [
            ("app/__init__.py", FIXTURE_PATH / "app/__init__.py"),
        ], "style: Code cleanup and formatting")
        
        # Commit 13: Update dependencies
        logger.info("  13/15: Update dependencies")
        self._commit_files(repo, [
            ("requirements.txt", FIXTURE_PATH / "requirements.txt"),
        ], "chore: Update dependencies")
        
        # Commit 14: Improve gitignore
        logger.info("  14/15: Update gitignore")
        self._commit_files(repo, [
            (".gitignore", FIXTURE_PATH / ".gitignore"),
        ], "chore: Update .gitignore")
        
        # Commit 15: Final polish
        logger.info("  15/15: Final polish")
        self._commit_files(repo, [
            ("README.md", FIXTURE_PATH / "README.md"),
            ("app/main.py", FIXTURE_PATH / "app/main.py"),
        ], "polish: Final improvements and documentation")
        
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


def reset_to_fixture_state(initial_commits: int = 3) -> str:
    """Reset repository to clean test-app state and apply fixture commits.
    
    This is the MAIN function for demos and tests - provides deterministic state:
    1. Deletes all existing commits
    2. Restores clean test-app template
    3. Applies initial fixture commits (default: 3 for bootstrap)
    
    Args:
        initial_commits: Number of commits to apply initially (1-15)
                        Default 3 leaves 12 commits for sync testing
    
    Returns:
        Repository full name
    """
    import shutil
    import subprocess
    from datetime import datetime, timedelta
    
    logger.info("\n" + "="*80)
    logger.info("  🔄 RESETTING TO FIXTURE STATE")
    logger.info("="*80 + "\n")
    
    # Clone repository
    token = os.getenv("GITHUB_TOKEN")
    temp_dir = Path("/tmp/quality-guardian-fixture-reset")
    
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    repo_url = f"https://{token}@github.com/{TEST_REPO_FULL}.git"
    
    logger.info(f"📥 Cloning {TEST_REPO_FULL}...")
    subprocess.run(
        ["git", "clone", repo_url, str(temp_dir)],
        check=True,
        capture_output=True
    )
    
    # Remove all files except .git
    logger.info("🗑️  Removing existing files...")
    for item in temp_dir.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    
    # Copy test-app template
    logger.info(f"📋 Copying test-app template...")
    for item in FIXTURE_PATH.iterdir():
        if item.name == ".git":
            continue
        
        dest = temp_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    
    # Commit clean state
    logger.info("💾 Committing clean state...")
    subprocess.run(["git", "add", "-A"], cwd=temp_dir, check=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: Reset to test-app template"],
        cwd=temp_dir,
        check=True,
        capture_output=True
    )
    
    # Apply initial fixture commits (leaving some for sync)
    logger.info(f"📦 Applying {initial_commits} fixture commits...")
    _apply_fixture_commits(temp_dir, start=0, count=initial_commits)
    
    # Force push
    logger.info("🚀 Force pushing to origin...")
    subprocess.run(
        ["git", "push", "--force", "origin", "main"],
        cwd=temp_dir,
        check=True,
        capture_output=True
    )
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    logger.info("\n✅ Repository reset complete!\n")
    return TEST_REPO_FULL


def apply_remaining_fixture_commits(start_from: int = 4) -> int:
    """Apply remaining fixture commits for sync testing.
    
    Use this after reset_to_fixture_state() to add more commits
    that sync agent can detect.
    
    Args:
        start_from: Which commit to start from (1-15)
        
    Returns:
        Number of commits applied
    """
    import shutil
    import subprocess
    
    logger.info(f"\n📦 Adding remaining fixture commits (from #{start_from})...")
    
    token = os.getenv("GITHUB_TOKEN")
    temp_dir = Path("/tmp/quality-guardian-add-commits")
    
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    # Clone
    repo_url = f"https://{token}@github.com/{TEST_REPO_FULL}.git"
    subprocess.run(
        ["git", "clone", repo_url, str(temp_dir)],
        check=True,
        capture_output=True
    )
    
    # Apply remaining commits
    remaining = 15 - start_from + 1  # e.g., start_from=4 → commits 4-15 → 12 commits
    _apply_fixture_commits(temp_dir, start=start_from - 1, count=remaining)
    
    # Push
    logger.info("🚀 Pushing new commits...")
    subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=temp_dir,
        check=True,
        capture_output=True
    )
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    logger.info(f"✅ Added {remaining} commits!\n")
    return remaining


def _apply_fixture_commits(repo_path: Path, start: int = 0, count: int = 5):
    """Apply fixture commits from fixtures/commits/ directory.
    
    Args:
        repo_path: Path to git repository
        start: Starting index (0-14)
        count: Number of commits to apply
    """
    from datetime import datetime, timedelta
    import importlib.util
    
    commits_dir = Path(__file__).parent / "commits"
    
    all_commits = [
        "commit_01_add_logging",
        "commit_02_fix_sql_injection",
        "commit_03_add_password_validation",
        "commit_04_refactor_config",
        "commit_05_add_validation",
        "commit_06_remove_validation",
        "commit_07_add_unsafe_feature",
        "commit_08_fix_upload_validation",
        "commit_09_restore_search_validation",
        "commit_10_add_caching",
        "commit_11_add_metrics",
        "commit_12_remove_eval",
        "commit_13_add_auth",
        "commit_14_rushed_feature",
        "commit_15_disable_logging",
    ]
    
    # Select commits to apply
    commit_files = all_commits[start:start + count]
    
    base_date = datetime.now()
    
    for i, commit_name in enumerate(commit_files):
        commit_file = commits_dir / f"{commit_name}.py"
        
        if not commit_file.exists():
            logger.warning(f"Commit fixture not found: {commit_file}")
            continue
        
        # Import commit module
        spec = importlib.util.spec_from_file_location(commit_name, commit_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        logger.info(f"  {i+1}/{count}: {module.COMMIT_MESSAGE}")
        
        # Apply changes by writing files directly
        if hasattr(module, 'FILES'):
            # New format: FILES dict with full file contents
            for file_path, content in module.FILES.items():
                full_path = repo_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
        elif hasattr(module, 'DIFF'):
            # Legacy format: git diff (try to apply)
            diff_file = repo_path / ".temp.patch"
            diff_file.write_text(module.DIFF, encoding='utf-8')
            
            try:
                subprocess.run(
                    ["patch", "-p1", "-i", str(diff_file)],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to apply patch: {e.stderr}")
                raise
            finally:
                if diff_file.exists():
                    diff_file.unlink()
        else:
            logger.error(f"Commit module {commit_name} has neither FILES nor DIFF")
            raise ValueError("Invalid commit fixture format")
        
        # Stage and commit
        subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)
        
        # Commit with proper date (1 hour apart)
        commit_date = base_date - timedelta(hours=count - i - 1)
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = module.AUTHOR
        env["GIT_AUTHOR_EMAIL"] = module.AUTHOR_EMAIL
        env["GIT_COMMITTER_NAME"] = module.AUTHOR
        env["GIT_COMMITTER_EMAIL"] = module.AUTHOR_EMAIL
        env["GIT_AUTHOR_DATE"] = commit_date.isoformat()
        env["GIT_COMMITTER_DATE"] = commit_date.isoformat()
        
        subprocess.run(
            ["git", "commit", "-m", module.COMMIT_MESSAGE],
            cwd=repo_path,
            env=env,
            check=True,
            capture_output=True
        )
