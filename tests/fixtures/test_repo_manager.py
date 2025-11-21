"""Test repository manager for integration testing.

Manages lifecycle of test repository:
- Create repo if needed (once per machine)
- Create fresh PRs for each test session
- Cleanup PRs after tests
- Never delete the repo (reuse across sessions)
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from github import Github, GithubException


class TestRepoManager:
    """Manages test repository for integration testing."""

    REPO_NAME = "test-code-review-app"

    def __init__(self, github_token: str):
        """Initialize manager.

        Args:
            github_token: GitHub personal access token
        """
        self.token = github_token
        self.gh = Github(github_token)
        self.user = self.gh.get_user()
        self.repo_full_name = f"{self.user.login}/{self.REPO_NAME}"
        self.repo = None
        self.created_prs = []
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    def setup(self) -> Dict[str, Any]:
        """Setup test repository and create fresh PRs.

        Returns:
            Dict with repo_name and PR numbers
        """
        # Ensure repository exists
        self._ensure_repo_exists()

        # Initialize with test app if empty
        self._ensure_initialized()

        # Create fresh PRs for this test session
        pr_security = self._create_pr_security()
        pr_complexity = self._create_pr_complexity()
        pr_clean = self._create_pr_clean()

        return {
            "repo_name": self.repo_full_name,
            "pr_security": pr_security.number,
            "pr_complexity": pr_complexity.number,
            "pr_clean": pr_clean.number,
        }

    def cleanup(self):
        """Cleanup test PRs created in this session.

        Note: Does NOT delete repository - it's reused across sessions.
        Only closes PRs and deletes their branches.
        """
        for pr in self.created_prs:
            try:
                # Close PR
                pr.edit(state="closed")

                # Delete branch
                ref = f"heads/{pr.head.ref}"
                try:
                    self.repo.get_git_ref(ref).delete()
                except GithubException:
                    pass  # Branch already deleted

            except GithubException as e:
                print(f"Warning: Failed to cleanup PR #{pr.number}: {e}")

    def _ensure_repo_exists(self):
        """Create repository if it doesn't exist, otherwise use existing."""
        try:
            self.repo = self.gh.get_repo(self.repo_full_name)
            print(f"   ℹ Using existing repository: {self.repo.html_url}")
        except GithubException as e:
            if e.status == 404:
                # Create new repository
                self.repo = self.user.create_repo(
                    name=self.REPO_NAME,
                    description="Test repository for AI Code Review Bot integration tests",
                    private=False,
                    auto_init=True,
                    has_issues=True,
                    has_projects=False,
                    has_wiki=False,
                )
                print(f"   ✓ Created repository: {self.repo.html_url}")
            else:
                raise

    def _ensure_initialized(self):
        """Initialize repository with test application if needed."""
        # Check if repo has test application files
        try:
            self.repo.get_contents("app/main.py")
            print("   ℹ Repository already initialized with test app")
            return
        except GithubException:
            pass  # Need to initialize

        print("   ℹ Initializing repository with test application...")
        self._initialize_test_app()

    def _initialize_test_app(self):
        """Copy test-app from v1 fixtures to repository."""
        # Find test-app from v1
        project_root = Path(__file__).parent.parent.parent
        test_app_path = project_root.parent / "capstone" / "tests" / "fixtures" / "test-app"

        if not test_app_path.exists():
            raise FileNotFoundError(f"Test app not found: {test_app_path}")

        # Clone repo to temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir) / self.REPO_NAME
            clone_url = f"https://{self.token}@github.com/{self.repo_full_name}.git"

            # Clone
            os.system(f"git clone {clone_url} {tmppath} > /dev/null 2>&1")

            # Copy test-app files
            for item in test_app_path.iterdir():
                if item.name in [".git", "__pycache__"]:
                    continue

                dest = tmppath / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

            # Commit and push
            os.chdir(tmppath)
            os.system("git add -A")
            os.system('git commit -m "Initialize with test application" > /dev/null 2>&1')
            os.system("git push origin main > /dev/null 2>&1")

        print("   ✓ Test application initialized")

    def _create_pr_security(self):
        """Create PR with security vulnerabilities."""
        branch_name = f"test/security-{self.session_id}"
        base_branch = self.repo.default_branch
        base_sha = self.repo.get_branch(base_branch).commit.sha

        # Create branch
        self.repo.create_git_ref(f"refs/heads/{branch_name}", base_sha)

        # Create file with security issues
        code = '''"""Security test - intentional vulnerabilities."""
import subprocess
import pickle


def execute_user_command(user_input):
    """SECURITY: Shell injection vulnerability."""
    result = subprocess.call(user_input, shell=True)
    return result


def load_untrusted_data(data_file):
    """SECURITY: Unsafe deserialization."""
    with open(data_file, 'rb') as f:
        return pickle.load(f)


def hardcoded_credentials():
    """SECURITY: Hardcoded secrets."""
    api_key = "sk-1234567890abcdef"
    return api_key
'''

        self.repo.create_file(
            path="app/insecure.py",
            message="Add security test code",
            content=code,
            branch=branch_name,
        )

        # Create PR
        pr = self.repo.create_pull(
            title=f"[TEST] Security issues - {self.session_id}",
            body="Test PR with intentional security vulnerabilities.",
            head=branch_name,
            base=base_branch,
        )

        self.created_prs.append(pr)
        print(f"   ✓ Created PR #{pr.number}: Security issues")
        return pr

    def _create_pr_complexity(self):
        """Create PR with high complexity functions."""
        branch_name = f"test/complexity-{self.session_id}"
        base_branch = self.repo.default_branch
        base_sha = self.repo.get_branch(base_branch).commit.sha

        self.repo.create_git_ref(f"refs/heads/{branch_name}", base_sha)

        code = '''"""Complexity test - intentionally complex functions."""


def super_complex_processor(a, b, c, d, e, f):
    """COMPLEXITY: Cyclomatic complexity = 23."""
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if a > b:
                                if b > c:
                                    if c > d:
                                        if d > e:
                                            if e > f:
                                                return a + b + c
                                            else:
                                                return a - b
                                        else:
                                            return b - c
                                    else:
                                        return c - d
                                else:
                                    return d - e
                            else:
                                return e - f
                        else:
                            return a * b
                    else:
                        return b * c
                else:
                    return c * d
            else:
                return d * e
        else:
            return e * f
    return 0
'''

        self.repo.create_file(
            path="app/complex.py",
            message="Add complexity test code",
            content=code,
            branch=branch_name,
        )

        pr = self.repo.create_pull(
            title=f"[TEST] Complexity issues - {self.session_id}",
            body="Test PR with high complexity functions.",
            head=branch_name,
            base=base_branch,
        )

        self.created_prs.append(pr)
        print(f"   ✓ Created PR #{pr.number}: Complexity issues")
        return pr

    def _create_pr_clean(self):
        """Create PR with clean code."""
        branch_name = f"test/clean-{self.session_id}"
        base_branch = self.repo.default_branch
        base_sha = self.repo.get_branch(base_branch).commit.sha

        self.repo.create_git_ref(f"refs/heads/{branch_name}", base_sha)

        code = '''"""Clean code example."""


def calculate_total(items: list) -> float:
    """Calculate total price."""
    return sum(item.get('price', 0.0) for item in items)


def format_name(first: str, last: str) -> str:
    """Format display name."""
    return f"{first} {last}".strip()
'''

        self.repo.create_file(
            path="app/helpers.py",
            message="Add helper functions",
            content=code,
            branch=branch_name,
        )

        pr = self.repo.create_pull(
            title=f"[TEST] Clean code - {self.session_id}",
            body="Test PR with clean, well-written code.",
            head=branch_name,
            base=base_branch,
        )

        self.created_prs.append(pr)
        print(f"   ✓ Created PR #{pr.number}: Clean code")
        return pr
