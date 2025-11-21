"""Integration tests for PR context loader.

These tests use real GitHub API calls to validate functionality.
"""

import pytest
from src.github import GitHubClient, PRContextLoader


@pytest.mark.integration
def test_load_pr_context(github_token: str, test_repo: str, test_pr_number: int):
    """Test loading complete PR context."""
    client = GitHubClient(github_token)
    loader = PRContextLoader(client)
    
    context = loader.load(test_repo, test_pr_number)
    
    # Validate basic PR info
    assert context.repo_full_name == test_repo
    assert context.pr_number == test_pr_number
    assert context.title is not None
    assert context.author is not None
    assert context.base_branch is not None
    assert context.head_branch is not None
    assert context.created_at is not None
    assert context.updated_at is not None
    
    # Validate files
    assert isinstance(context.files, list)
    assert len(context.files) > 0
    file = context.files[0]
    assert file.filename is not None
    assert file.status in ["added", "modified", "removed", "renamed"]
    assert file.additions >= 0
    assert file.deletions >= 0
    
    # Validate diff
    assert isinstance(context.diff, str)
    assert len(context.diff) > 0
    assert "diff --git" in context.diff
    
    # Validate comments (may be empty)
    assert isinstance(context.review_comments, list)
    assert isinstance(context.issue_comments, list)
    
    # Validate metadata
    assert isinstance(context.labels, list)
    assert isinstance(context.is_draft, bool)


@pytest.mark.integration
def test_pr_context_with_comments(github_token: str, test_repo: str, test_pr_number: int):
    """Test PR context includes comments if they exist."""
    client = GitHubClient(github_token)
    loader = PRContextLoader(client)
    
    # Create a test comment
    comment = client.create_pr_comment(
        test_repo,
        test_pr_number,
        "🤖 Test comment for context loading",
    )
    
    try:
        # Load context
        context = loader.load(test_repo, test_pr_number)
        
        # Verify comment is included
        assert len(context.issue_comments) > 0
        comment_found = any(
            c.body == "🤖 Test comment for context loading"
            for c in context.issue_comments
        )
        assert comment_found
    finally:
        # Cleanup
        comment.delete()


@pytest.mark.integration
def test_pr_context_file_changes(github_token: str, test_repo: str, test_pr_number: int):
    """Test PR context correctly represents file changes."""
    client = GitHubClient(github_token)
    loader = PRContextLoader(client)
    
    context = loader.load(test_repo, test_pr_number)
    
    # Verify file changes have patches
    files_with_patches = [f for f in context.files if f.patch]
    assert len(files_with_patches) > 0
    
    # Verify patch format
    for file in files_with_patches:
        # Patch should contain diff hunks
        assert "@@ " in file.patch or len(file.patch) > 0
