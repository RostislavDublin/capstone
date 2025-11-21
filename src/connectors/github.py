"""GitHub connector implementation using PyGithub."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests
from github import Auth, Github
from github.Commit import Commit
from github.Repository import Repository
from github.Tag import Tag

from .base import CommitInfo, RepositoryConnector, RepositoryInfo, TagInfo


class GitHubConnector(RepositoryConnector):
    """GitHub-specific implementation of repository connector."""

    def __init__(self, token: str):
        """Initialize GitHub connector with authentication.

        Args:
            token: GitHub personal access token or app token
        """
        auth = Auth.Token(token)
        self._client = Github(auth=auth)

    def _get_repository(self, repo_identifier: str) -> Repository:
        """Get repository object by identifier.

        Args:
            repo_identifier: Repository in format "owner/repo"

        Returns:
            PyGithub Repository object
        """
        return self._client.get_repo(repo_identifier)

    def get_repository_info(self, repo_identifier: str) -> RepositoryInfo:
        """Get basic repository metadata.

        Args:
            repo_identifier: Repository in format "owner/repo"

        Returns:
            RepositoryInfo with metadata
        """
        repo = self._get_repository(repo_identifier)
        return RepositoryInfo(
            full_name=repo.full_name,
            owner=repo.owner.login,
            name=repo.name,
            description=repo.description,
            default_branch=repo.default_branch,
            created_at=repo.created_at,
            language=repo.language,
            topics=repo.get_topics(),
        )

    def list_commits(
        self,
        repo_identifier: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        branch: Optional[str] = None,
    ) -> List[CommitInfo]:
        """List commits with optional date filtering.

        Args:
            repo_identifier: Repository in format "owner/repo"
            since: Only commits after this date (inclusive)
            until: Only commits before this date (inclusive)
            branch: Branch name (defaults to default branch)

        Returns:
            List of CommitInfo objects, newest first
        """
        repo = self._get_repository(repo_identifier)
        sha = branch if branch else repo.default_branch

        # PyGithub get_commits accepts since/until
        commits = repo.get_commits(sha=sha, since=since, until=until)

        result = []
        for commit in commits:
            # Get file changes from commit details
            files = commit.files if commit.files else []
            result.append(
                CommitInfo(
                    sha=commit.sha,
                    message=commit.commit.message,
                    author=commit.commit.author.name,
                    author_email=commit.commit.author.email,
                    date=commit.commit.author.date,
                    files_changed=[f.filename for f in files],
                    additions=commit.stats.additions,
                    deletions=commit.stats.deletions,
                )
            )

        return result

    def list_tags(self, repo_identifier: str) -> List[TagInfo]:
        """List all tags/releases in repository.

        Args:
            repo_identifier: Repository in format "owner/repo"

        Returns:
            List of TagInfo objects, newest first
        """
        repo = self._get_repository(repo_identifier)
        tags = repo.get_tags()

        result = []
        for tag in tags:
            # Get commit date from tag's commit
            commit = repo.get_commit(tag.commit.sha)
            result.append(
                TagInfo(
                    name=tag.name,
                    sha=tag.commit.sha,
                    date=commit.commit.author.date,
                    message=commit.commit.message,
                )
            )

        # Sort by date descending (newest first)
        result.sort(key=lambda t: t.date, reverse=True)
        return result

    def get_commit_diff(self, repo_identifier: str, sha: str) -> str:
        """Get unified diff for a specific commit.

        Args:
            repo_identifier: Repository in format "owner/repo"
            sha: Commit SHA

        Returns:
            Unified diff string
        """
        # PyGithub doesn't expose commit diff directly, use raw API
        response = requests.get(
            f"https://api.github.com/repos/{repo_identifier}/commits/{sha}",
            headers={
                "Accept": "application/vnd.github.v3.diff",
                "Authorization": f"token {self._client._Github__requester.auth.token}",
            },
        )
        response.raise_for_status()
        return response.text

    def clone_repository(
        self, repo_identifier: str, target_path: str, sha: Optional[str] = None
    ) -> str:
        """Clone repository using git CLI.

        Args:
            repo_identifier: Repository in format "owner/repo"
            target_path: Local filesystem path for clone
            sha: Optional commit SHA to checkout

        Returns:
            Absolute path to cloned repository
        """
        repo = self._get_repository(repo_identifier)
        clone_url = repo.clone_url

        # Create target directory
        target = Path(target_path)
        target.mkdir(parents=True, exist_ok=True)

        # Clone repository
        subprocess.run(
            ["git", "clone", clone_url, str(target)],
            check=True,
            capture_output=True,
            text=True,
        )

        # Checkout specific SHA if provided
        if sha:
            subprocess.run(
                ["git", "checkout", sha],
                cwd=str(target),
                check=True,
                capture_output=True,
                text=True,
            )

        return str(target.absolute())
