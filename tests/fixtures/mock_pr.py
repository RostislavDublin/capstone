"""Mock PR context for local testing without GitHub API.

Creates synthetic PullRequest objects from changesets for unit/integration tests.
"""

from typing import Optional
from datetime import datetime
from pathlib import Path

from capstone.models import (
    PullRequest,
    PRFile,
    PRAuthor,
    PRMetadata,
    PRDiff
)
from capstone.changesets import Changeset
from capstone.tools.diff_generator import generate_diff_from_changeset


def create_mock_pr_author(
    login: str = "testuser",
    name: str = "Test User",
    email: str = "test@example.com"
) -> PRAuthor:
    """Create mock PR author."""
    return PRAuthor(
        login=login,
        name=name,
        email=email,
        avatar_url=f"https://avatars.githubusercontent.com/{login}"
    )


def create_mock_pr_file(
    filename: str,
    status: str,
    additions: int,
    deletions: int,
    changes: int,
    patch: str
) -> PRFile:
    """Create mock PR file change."""
    return PRFile(
        filename=filename,
        status=status,
        additions=additions,
        deletions=deletions,
        changes=changes,
        patch=patch
    )


def create_mock_pr_from_changeset(
    changeset: Changeset,
    pr_number: int = 1,
    base_path: Optional[Path] = None,
    repo_name: str = "RostislavDublin/code-review-test-fixture"
) -> PullRequest:
    """Create mock PullRequest from Changeset definition.
    
    Args:
        changeset: Changeset to convert to PR
        pr_number: PR number to assign
        base_path: Optional path to test-fixture for generating realistic diffs
        repo_name: Repository name (owner/repo)
        
    Returns:
        PullRequest object ready for agent testing
        
    Example:
        >>> from capstone.changesets import CHANGESET_01_SQL_INJECTION
        >>> pr = create_mock_pr_from_changeset(CHANGESET_01_SQL_INJECTION)
        >>> # Now test agent with this PR
        >>> result = await agent.review_pr(pr)
    """
    # Generate diff
    diff_text = generate_diff_from_changeset(changeset, base_path)
    
    # Count additions/deletions from diff
    additions = sum(1 for line in diff_text.split("\n") if line.startswith("+"))
    deletions = sum(1 for line in diff_text.split("\n") if line.startswith("-"))
    
    # Create file object
    status_map = {
        "add": "added",
        "modify": "modified",
        "replace": "modified"
    }
    
    pr_file = create_mock_pr_file(
        filename=changeset.target_file,
        status=status_map[changeset.operation],
        additions=additions,
        deletions=deletions,
        changes=additions + deletions,
        patch=diff_text
    )
    
    # Create metadata
    metadata = PRMetadata(
        number=pr_number,
        title=changeset.pr_title,
        body=changeset.pr_body,
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        base_branch="main",
        head_branch=changeset.branch_name,
        mergeable=True,
        draft=False,
        labels=[changeset.category.value] if changeset.category else []
    )
    
    # Create diff
    pr_diff = PRDiff(
        total_additions=additions,
        total_deletions=deletions,
        changed_files_count=1,
        files=[pr_file],
        base_sha="abc123",
        head_sha="def456"
    )
    
    # Create author
    author = create_mock_pr_author()
    
    # Assemble PR
    return PullRequest(
        url=f"https://github.com/{repo_name}/pull/{pr_number}",
        repo_name=repo_name,
        author=author,
        metadata=metadata,
        diff=pr_diff
    )


def create_all_mock_prs(base_path: Optional[Path] = None) -> list[PullRequest]:
    """Create mock PRs for all changesets.
    
    Args:
        base_path: Optional path to test-fixture directory
        
    Returns:
        List of PullRequest objects, one per changeset
        
    Example:
        >>> prs = create_all_mock_prs()
        >>> for pr in prs:
        ...     result = await agent.review_pr(pr)
    """
    from capstone.changesets import ALL_CHANGESETS
    
    return [
        create_mock_pr_from_changeset(changeset, pr_number=i+1, base_path=base_path)
        for i, changeset in enumerate(ALL_CHANGESETS)
    ]


def create_mock_pr_context_dict(changeset: Changeset) -> dict:
    """Create minimal PR context as dict for simple tests.
    
    Args:
        changeset: Changeset to extract context from
        
    Returns:
        Dict with PR metadata suitable for basic agent tests
        
    Example:
        >>> from capstone.changesets import CHANGESET_01_SQL_INJECTION
        >>> context = create_mock_pr_context_dict(CHANGESET_01_SQL_INJECTION)
        >>> # Simpler alternative to full PullRequest object
    """
    return {
        "title": changeset.pr_title,
        "body": changeset.pr_body,
        "branch": changeset.branch_name,
        "file": changeset.target_file,
        "operation": changeset.operation,
        "category": changeset.category.value if changeset.category else None,
        "expected_issues": len(changeset.expected_issues),
        "critical_issues": sum(
            1 for issue in changeset.expected_issues if issue.severity == "critical"
        )
    }
