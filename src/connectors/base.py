"""Abstract base class for repository connectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class CommitInfo:
    """Information about a repository commit."""

    sha: str
    message: str
    author: str
    author_email: str
    date: datetime
    files_changed: List[str]
    additions: int
    deletions: int


@dataclass
class TagInfo:
    """Information about a repository tag/release."""

    name: str
    sha: str
    date: datetime
    message: Optional[str] = None


@dataclass
class RepositoryInfo:
    """Basic repository metadata."""

    full_name: str
    owner: str
    name: str
    description: Optional[str]
    default_branch: str
    created_at: datetime
    language: Optional[str]
    topics: List[str]


class RepositoryConnector(ABC):
    """Abstract interface for accessing Git hosting platforms."""

    @abstractmethod
    def get_repository_info(self, repo_identifier: str) -> RepositoryInfo:
        """Get basic repository metadata.

        Args:
            repo_identifier: Platform-specific repository identifier
                            (e.g., "owner/repo" for GitHub)

        Returns:
            RepositoryInfo object with metadata
        """
        pass

    @abstractmethod
    def list_commits(
        self,
        repo_identifier: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        branch: Optional[str] = None,
    ) -> List[CommitInfo]:
        """List commits in repository with optional filtering.

        Args:
            repo_identifier: Platform-specific repository identifier
            since: Only commits after this date (inclusive)
            until: Only commits before this date (inclusive)
            branch: Branch name (defaults to repository's default branch)

        Returns:
            List of CommitInfo objects, newest first
        """
        pass

    @abstractmethod
    def list_tags(self, repo_identifier: str) -> List[TagInfo]:
        """List all tags/releases in repository.

        Args:
            repo_identifier: Platform-specific repository identifier

        Returns:
            List of TagInfo objects, newest first
        """
        pass

    @abstractmethod
    def get_commit_diff(self, repo_identifier: str, sha: str) -> str:
        """Get unified diff for a specific commit.

        Args:
            repo_identifier: Platform-specific repository identifier
            sha: Commit SHA

        Returns:
            Unified diff string
        """
        pass

    @abstractmethod
    def clone_repository(
        self, repo_identifier: str, target_path: str, sha: Optional[str] = None
    ) -> str:
        """Clone repository to local filesystem.

        Args:
            repo_identifier: Platform-specific repository identifier
            target_path: Local filesystem path for clone
            sha: Optional commit SHA to checkout (defaults to HEAD)

        Returns:
            Absolute path to cloned repository
        """
        pass
