"""GitHub API client wrapper using PyGithub."""

from typing import Optional, List
from github import Github, Auth
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.PullRequestComment import PullRequestComment
from github.IssueComment import IssueComment


class GitHubClient:
    """Wrapper around PyGithub for PR operations."""

    def __init__(self, token: str):
        """Initialize GitHub client with authentication token.
        
        Args:
            token: GitHub personal access token or app token
        """
        auth = Auth.Token(token)
        self._client = Github(auth=auth)

    def get_repository(self, repo_full_name: str) -> Repository:
        """Get repository by full name (owner/repo).
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            
        Returns:
            GitHub Repository object
        """
        return self._client.get_repo(repo_full_name)

    def get_pull_request(self, repo_full_name: str, pr_number: int) -> PullRequest:
        """Get pull request by number.
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            GitHub PullRequest object
        """
        repo = self.get_repository(repo_full_name)
        return repo.get_pull(pr_number)

    def get_pr_diff(self, repo_full_name: str, pr_number: int) -> str:
        """Get unified diff for pull request.
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            Unified diff string
        """
        pr = self.get_pull_request(repo_full_name, pr_number)
        # PyGithub doesn't expose diff directly, use requests
        import requests
        response = requests.get(
            pr.url,
            headers={
                "Accept": "application/vnd.github.v3.diff",
                "Authorization": f"token {self._client._Github__requester.auth.token}",
            },
        )
        response.raise_for_status()
        return response.text

    def get_pr_files(self, repo_full_name: str, pr_number: int) -> List[dict]:
        """Get list of files changed in PR.
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            List of file objects with filename, status, additions, deletions, patch
        """
        pr = self.get_pull_request(repo_full_name, pr_number)
        files = []
        for file in pr.get_files():
            files.append({
                "filename": file.filename,
                "status": file.status,
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes,
                "patch": file.patch if file.patch else "",
            })
        return files

    def get_pr_review_comments(
        self, repo_full_name: str, pr_number: int
    ) -> List[PullRequestComment]:
        """Get all review comments (inline comments on diff).
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            List of PullRequestComment objects
        """
        pr = self.get_pull_request(repo_full_name, pr_number)
        return list(pr.get_review_comments())

    def get_pr_issue_comments(
        self, repo_full_name: str, pr_number: int
    ) -> List[IssueComment]:
        """Get all issue comments (general PR conversation).
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            List of IssueComment objects
        """
        pr = self.get_pull_request(repo_full_name, pr_number)
        return list(pr.get_issue_comments())

    def create_review_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
        path: str,
        line: int,
    ) -> PullRequestComment:
        """Create inline review comment on specific line.
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            body: Comment text (supports markdown)
            path: Relative file path
            line: Line number in diff (right side)
            
        Returns:
            Created PullRequestComment object
        """
        pr = self.get_pull_request(repo_full_name, pr_number)
        return pr.create_review_comment(
            body=body,
            commit=pr.get_commits()[pr.commits - 1],  # Latest commit
            path=path,
            line=line,
        )

    def reply_to_review_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        comment_id: int,
        body: str,
    ) -> PullRequestComment:
        """Reply to existing review comment (creates thread).
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            comment_id: ID of comment to reply to
            body: Reply text (supports markdown)
            
        Returns:
            Created PullRequestComment object
        """
        pr = self.get_pull_request(repo_full_name, pr_number)
        # Reply by creating a new comment with in_reply_to
        return pr.create_review_comment(
            body=body,
            commit=pr.get_commits()[pr.commits - 1],
            path=pr.get_review_comment(comment_id).path,
            line=pr.get_review_comment(comment_id).line or pr.get_review_comment(comment_id).original_line,
            in_reply_to=comment_id,
        )

    def create_pr_comment(
        self, repo_full_name: str, pr_number: int, body: str
    ) -> IssueComment:
        """Create general PR comment (not tied to specific line).
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            body: Comment text (supports markdown)
            
        Returns:
            Created IssueComment object
        """
        pr = self.get_pull_request(repo_full_name, pr_number)
        return pr.create_issue_comment(body)
