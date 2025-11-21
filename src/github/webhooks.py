"""GitHub webhook event handling."""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class WebhookEvent(Enum):
    """GitHub webhook event types we handle."""

    PR_OPENED = "pull_request.opened"
    PR_SYNCHRONIZE = "pull_request.synchronize"  # New commits pushed
    PR_REOPENED = "pull_request.reopened"
    REVIEW_COMMENT_CREATED = "pull_request_review_comment.created"
    ISSUE_COMMENT_CREATED = "issue_comment.created"
    UNKNOWN = "unknown"


@dataclass
class WebhookPayload:
    """Parsed webhook payload."""

    event: WebhookEvent
    repo_full_name: str
    pr_number: int
    sender: str
    
    # Optional fields depending on event type
    comment_id: Optional[int] = None
    comment_body: Optional[str] = None
    comment_path: Optional[str] = None
    comment_line: Optional[int] = None


class WebhookHandler:
    """Handles GitHub webhook events."""

    def parse(self, event_type: str, payload: Dict[str, Any]) -> WebhookPayload:
        """Parse webhook payload into structured format.
        
        Args:
            event_type: GitHub event type (e.g., "pull_request", "issue_comment")
            payload: Raw webhook JSON payload
            
        Returns:
            Parsed WebhookPayload
        """
        action = payload.get("action", "")
        event_key = f"{event_type}.{action}"
        
        # Map to our event enum
        event = WebhookEvent.UNKNOWN
        if event_key == "pull_request.opened":
            event = WebhookEvent.PR_OPENED
        elif event_key == "pull_request.synchronize":
            event = WebhookEvent.PR_SYNCHRONIZE
        elif event_key == "pull_request.reopened":
            event = WebhookEvent.PR_REOPENED
        elif event_key == "pull_request_review_comment.created":
            event = WebhookEvent.REVIEW_COMMENT_CREATED
        elif event_key == "issue_comment.created":
            # Only handle PR comments, not issues
            if "pull_request" in payload.get("issue", {}):
                event = WebhookEvent.ISSUE_COMMENT_CREATED
        
        # Extract common fields
        repo_full_name = payload["repository"]["full_name"]
        pr_number = payload["pull_request"]["number"] if "pull_request" in payload else payload["issue"]["number"]
        sender = payload["sender"]["login"]
        
        # Extract comment-specific fields
        comment_id = None
        comment_body = None
        comment_path = None
        comment_line = None
        
        if event == WebhookEvent.REVIEW_COMMENT_CREATED:
            comment = payload["comment"]
            comment_id = comment["id"]
            comment_body = comment["body"]
            comment_path = comment["path"]
            comment_line = comment["line"] if "line" in comment else comment.get("original_line")
        elif event == WebhookEvent.ISSUE_COMMENT_CREATED:
            comment = payload["comment"]
            comment_id = comment["id"]
            comment_body = comment["body"]
        
        return WebhookPayload(
            event=event,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            sender=sender,
            comment_id=comment_id,
            comment_body=comment_body,
            comment_path=comment_path,
            comment_line=comment_line,
        )

    def should_process(self, payload: WebhookPayload) -> bool:
        """Determine if we should process this webhook event.
        
        Args:
            payload: Parsed webhook payload
            
        Returns:
            True if we should trigger bot action
        """
        # Don't process unknown events
        if payload.event == WebhookEvent.UNKNOWN:
            return False
        
        # Process all PR lifecycle events
        if payload.event in [
            WebhookEvent.PR_OPENED,
            WebhookEvent.PR_SYNCHRONIZE,
            WebhookEvent.PR_REOPENED,
        ]:
            return True
        
        # Process comments (for learning from feedback)
        if payload.event in [
            WebhookEvent.REVIEW_COMMENT_CREATED,
            WebhookEvent.ISSUE_COMMENT_CREATED,
        ]:
            # TODO: Add logic to detect if comment is responding to our bot
            # For now, process all comments
            return True
        
        return False
