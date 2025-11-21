"""PR context loading and representation."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from .client import GitHubClient


@dataclass
class ReviewComment:
    """Represents a review comment (inline on diff)."""

    id: int
    author: str
    body: str
    path: str
    line: int
    created_at: datetime
    in_reply_to_id: Optional[int] = None


@dataclass
class IssueComment:
    """Represents a general PR comment."""

    id: int
    author: str
    body: str
    created_at: datetime


@dataclass
class FileChange:
    """Represents a changed file in PR."""

    filename: str
    status: str  # added, modified, removed, renamed
    additions: int
    deletions: int
    changes: int
    patch: str


@dataclass
class PRContext:
    """Complete context of a pull request.
    
    This is the primary entity our agents work with.
    Contains all PR metadata, code changes, and conversation history.
    """

    repo_full_name: str
    pr_number: int
    title: str
    description: str
    author: str
    base_branch: str
    head_branch: str
    created_at: datetime
    updated_at: datetime
    
    # Code changes
    files: List[FileChange]
    diff: str
    
    # Conversation history
    review_comments: List[ReviewComment]
    issue_comments: List[IssueComment]
    
    # Metadata
    labels: List[str]
    is_draft: bool
    mergeable: Optional[bool]


class PRContextLoader:
    """Loads complete PR context from GitHub API."""

    def __init__(self, github_client: GitHubClient):
        """Initialize with GitHub client.
        
        Args:
            github_client: Authenticated GitHub API client
        """
        self.client = github_client

    def load(self, repo_full_name: str, pr_number: int) -> PRContext:
        """Load complete PR context.
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            PRContext with all PR data
        """
        # Get PR object
        pr = self.client.get_pull_request(repo_full_name, pr_number)
        
        # Load files
        files_data = self.client.get_pr_files(repo_full_name, pr_number)
        files = [
            FileChange(
                filename=f["filename"],
                status=f["status"],
                additions=f["additions"],
                deletions=f["deletions"],
                changes=f["changes"],
                patch=f["patch"],
            )
            for f in files_data
        ]
        
        # Load diff
        diff = self.client.get_pr_diff(repo_full_name, pr_number)
        
        # Load review comments (inline)
        review_comments_raw = self.client.get_pr_review_comments(repo_full_name, pr_number)
        review_comments = [
            ReviewComment(
                id=c.id,
                author=c.user.login,
                body=c.body,
                path=c.path,
                line=c.line if c.line else c.original_line,
                created_at=c.created_at,
                in_reply_to_id=c.in_reply_to_id if hasattr(c, 'in_reply_to_id') else None,
            )
            for c in review_comments_raw
        ]
        
        # Load issue comments (general)
        issue_comments_raw = self.client.get_pr_issue_comments(repo_full_name, pr_number)
        issue_comments = [
            IssueComment(
                id=c.id,
                author=c.user.login,
                body=c.body,
                created_at=c.created_at,
            )
            for c in issue_comments_raw
        ]
        
        # Build context
        return PRContext(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            title=pr.title,
            description=pr.body or "",
            author=pr.user.login,
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
            created_at=pr.created_at,
            updated_at=pr.updated_at,
            files=files,
            diff=diff,
            review_comments=review_comments,
            issue_comments=issue_comments,
            labels=[label.name for label in pr.labels],
            is_draft=pr.draft,
            mergeable=pr.mergeable,
        )
