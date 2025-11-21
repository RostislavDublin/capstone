"""Integration tests for GitHub client.

These tests use real GitHub API calls to validate functionality.
Set GITHUB_TOKEN in .env to run these tests.
"""

import pytest
from src.github import GitHubClient


@pytest.mark.integration
def test_get_repository(github_token: str, test_repo: str):
    """Test fetching repository."""
    client = GitHubClient(github_token)
    repo = client.get_repository(test_repo)
    
    assert repo.full_name == test_repo
    assert repo.owner is not None


@pytest.mark.integration
def test_get_pull_request(github_token: str, test_repo: str, test_pr_number: int):
    """Test fetching pull request."""
    client = GitHubClient(github_token)
    pr = client.get_pull_request(test_repo, test_pr_number)
    
    assert pr.number == test_pr_number
    assert pr.title is not None
    assert pr.user is not None


@pytest.mark.integration
def test_get_pr_diff(github_token: str, test_repo: str, test_pr_number: int):
    """Test fetching PR diff."""
    client = GitHubClient(github_token)
    diff = client.get_pr_diff(test_repo, test_pr_number)
    
    assert isinstance(diff, str)
    assert len(diff) > 0
    # Unified diff format starts with diff --git
    assert "diff --git" in diff


@pytest.mark.integration
def test_get_pr_files(github_token: str, test_repo: str, test_pr_number: int):
    """Test fetching PR files."""
    client = GitHubClient(github_token)
    files = client.get_pr_files(test_repo, test_pr_number)
    
    assert isinstance(files, list)
    assert len(files) > 0
    
    # Check file structure
    file = files[0]
    assert "filename" in file
    assert "status" in file
    assert "additions" in file
    assert "deletions" in file
    assert "changes" in file
    assert "patch" in file


@pytest.mark.integration
def test_get_pr_review_comments(github_token: str, test_repo: str, test_pr_number: int):
    """Test fetching review comments (inline on diff)."""
    client = GitHubClient(github_token)
    comments = client.get_pr_review_comments(test_repo, test_pr_number)
    
    assert isinstance(comments, list)
    # May be empty if no review comments exist
    if len(comments) > 0:
        comment = comments[0]
        assert comment.id is not None
        assert comment.body is not None
        assert comment.path is not None


@pytest.mark.integration
def test_get_pr_issue_comments(github_token: str, test_repo: str, test_pr_number: int):
    """Test fetching issue comments (general PR conversation)."""
    client = GitHubClient(github_token)
    comments = client.get_pr_issue_comments(test_repo, test_pr_number)
    
    assert isinstance(comments, list)
    # May be empty if no issue comments exist
    if len(comments) > 0:
        comment = comments[0]
        assert comment.id is not None
        assert comment.body is not None
        assert comment.user is not None


@pytest.mark.integration
def test_create_pr_comment(github_token: str, test_repo: str, test_pr_number: int):
    """Test creating general PR comment.
    
    Note: This creates a real comment. Use with test repo only.
    """
    client = GitHubClient(github_token)
    
    # Create comment
    comment = client.create_pr_comment(
        test_repo,
        test_pr_number,
        "🤖 Integration test comment - please ignore",
    )
    
    assert comment.id is not None
    assert comment.body == "🤖 Integration test comment - please ignore"
    
    # Cleanup: delete comment
    comment.delete()


@pytest.mark.integration
def test_create_review_comment(github_token: str, test_repo: str, test_pr_number: int):
    """Test creating inline review comment.
    
    Note: This creates a real comment. Use with test repo only.
    """
    client = GitHubClient(github_token)
    
    # First get files to find a valid path and line
    files = client.get_pr_files(test_repo, test_pr_number)
    if not files:
        pytest.skip("PR has no files to comment on")
    
    file = files[0]
    filename = file["filename"]
    
    # Parse patch to find a valid line number
    patch = file["patch"]
    if not patch:
        pytest.skip("File has no patch")
    
    # Find first added line (starts with +)
    line_number = None
    for i, line in enumerate(patch.split("\n"), 1):
        if line.startswith("+") and not line.startswith("+++"):
            line_number = i
            break
    
    if not line_number:
        pytest.skip("No added lines found in patch")
    
    # Create review comment
    comment = client.create_review_comment(
        test_repo,
        test_pr_number,
        "🤖 Integration test review comment - please ignore",
        filename,
        line_number,
    )
    
    assert comment.id is not None
    assert comment.body == "🤖 Integration test review comment - please ignore"
    assert comment.path == filename
    
    # Cleanup: delete comment
    comment.delete()


@pytest.mark.integration
def test_reply_to_review_comment(github_token: str, test_repo: str, test_pr_number: int):
    """Test replying to review comment (creates thread).
    
    Note: This creates real comments. Use with test repo only.
    """
    client = GitHubClient(github_token)
    
    # First create a comment to reply to
    files = client.get_pr_files(test_repo, test_pr_number)
    if not files or not files[0]["patch"]:
        pytest.skip("PR has no files to comment on")
    
    # Create initial comment
    initial_comment = client.create_review_comment(
        test_repo,
        test_pr_number,
        "🤖 Test parent comment",
        files[0]["filename"],
        1,
    )
    
    try:
        # Reply to it
        reply = client.reply_to_review_comment(
            test_repo,
            test_pr_number,
            initial_comment.id,
            "🤖 Test reply comment",
        )
        
        assert reply.id is not None
        assert reply.body == "🤖 Test reply comment"
        
        # Cleanup reply
        reply.delete()
    finally:
        # Cleanup initial comment
        initial_comment.delete()
