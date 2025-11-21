"""Integration tests for webhook handling.

These tests validate webhook payload parsing.
"""

import pytest
from src.github import WebhookHandler, WebhookEvent


@pytest.mark.integration
def test_parse_pr_opened_webhook():
    """Test parsing pull_request.opened webhook."""
    handler = WebhookHandler()
    
    # Minimal PR opened payload
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 123,
            "title": "Test PR",
        },
        "repository": {
            "full_name": "owner/repo",
        },
        "sender": {
            "login": "testuser",
        },
    }
    
    parsed = handler.parse("pull_request", payload)
    
    assert parsed.event == WebhookEvent.PR_OPENED
    assert parsed.repo_full_name == "owner/repo"
    assert parsed.pr_number == 123
    assert parsed.sender == "testuser"
    assert handler.should_process(parsed) is True


@pytest.mark.integration
def test_parse_pr_synchronize_webhook():
    """Test parsing pull_request.synchronize webhook (new commits)."""
    handler = WebhookHandler()
    
    payload = {
        "action": "synchronize",
        "pull_request": {
            "number": 123,
        },
        "repository": {
            "full_name": "owner/repo",
        },
        "sender": {
            "login": "testuser",
        },
    }
    
    parsed = handler.parse("pull_request", payload)
    
    assert parsed.event == WebhookEvent.PR_SYNCHRONIZE
    assert parsed.pr_number == 123
    assert handler.should_process(parsed) is True


@pytest.mark.integration
def test_parse_review_comment_webhook():
    """Test parsing pull_request_review_comment.created webhook."""
    handler = WebhookHandler()
    
    payload = {
        "action": "created",
        "pull_request": {
            "number": 123,
        },
        "comment": {
            "id": 456,
            "body": "This looks good!",
            "path": "src/main.py",
            "line": 42,
        },
        "repository": {
            "full_name": "owner/repo",
        },
        "sender": {
            "login": "reviewer",
        },
    }
    
    parsed = handler.parse("pull_request_review_comment", payload)
    
    assert parsed.event == WebhookEvent.REVIEW_COMMENT_CREATED
    assert parsed.pr_number == 123
    assert parsed.comment_id == 456
    assert parsed.comment_body == "This looks good!"
    assert parsed.comment_path == "src/main.py"
    assert parsed.comment_line == 42
    assert handler.should_process(parsed) is True


@pytest.mark.integration
def test_parse_issue_comment_webhook():
    """Test parsing issue_comment.created webhook on PR."""
    handler = WebhookHandler()
    
    payload = {
        "action": "created",
        "issue": {
            "number": 123,
            "pull_request": {},  # Indicates this is a PR, not issue
        },
        "comment": {
            "id": 789,
            "body": "General comment",
        },
        "repository": {
            "full_name": "owner/repo",
        },
        "sender": {
            "login": "commenter",
        },
    }
    
    parsed = handler.parse("issue_comment", payload)
    
    assert parsed.event == WebhookEvent.ISSUE_COMMENT_CREATED
    assert parsed.pr_number == 123
    assert parsed.comment_id == 789
    assert parsed.comment_body == "General comment"
    assert handler.should_process(parsed) is True


@pytest.mark.integration
def test_ignore_issue_comment_on_non_pr():
    """Test that issue comments on regular issues are ignored."""
    handler = WebhookHandler()
    
    payload = {
        "action": "created",
        "issue": {
            "number": 123,
            # No pull_request field - this is a regular issue
        },
        "comment": {
            "id": 789,
            "body": "Issue comment",
        },
        "repository": {
            "full_name": "owner/repo",
        },
        "sender": {
            "login": "commenter",
        },
    }
    
    parsed = handler.parse("issue_comment", payload)
    
    assert parsed.event == WebhookEvent.UNKNOWN
    assert handler.should_process(parsed) is False


@pytest.mark.integration
def test_ignore_unknown_event():
    """Test that unknown events are ignored."""
    handler = WebhookHandler()
    
    payload = {
        "action": "labeled",
        "pull_request": {
            "number": 123,
        },
        "repository": {
            "full_name": "owner/repo",
        },
        "sender": {
            "login": "testuser",
        },
    }
    
    parsed = handler.parse("pull_request", payload)
    
    assert parsed.event == WebhookEvent.UNKNOWN
    assert handler.should_process(parsed) is False
