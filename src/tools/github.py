"""GitHub API utilities and testing.

Research GitHub API endpoints, authentication, and comment formatting.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.File import File


class GitHubAPIClient:
    """Client for GitHub API operations."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (or from env)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN not provided")
        
        self.client = Github(self.token)
        self._rate_limit_checked = False
    
    def check_rate_limit(self) -> Dict[str, Any]:
        """Check GitHub API rate limits.
        
        Returns:
            Dict with rate limit info
        """
        rate_limit = self.client.get_rate_limit()
        return {
            "core": {
                "limit": rate_limit.core.limit,
                "remaining": rate_limit.core.remaining,
                "reset": rate_limit.core.reset
            },
            "search": {
                "limit": rate_limit.search.limit,
                "remaining": rate_limit.search.remaining,
                "reset": rate_limit.search.reset
            }
        }
    
    def get_repo(self, repo_full_name: str) -> Repository:
        """Get repository object.
        
        Args:
            repo_full_name: Repository name (owner/repo)
            
        Returns:
            Repository object
        """
        return self.client.get_repo(repo_full_name)
    
    def get_pr(self, repo_full_name: str, pr_number: int) -> PullRequest:
        """Get pull request object.
        
        Args:
            repo_full_name: Repository name
            pr_number: PR number
            
        Returns:
            PullRequest object
        """
        repo = self.get_repo(repo_full_name)
        return repo.get_pull(pr_number)
    
    def get_pr_files(self, pr: PullRequest) -> List[File]:
        """Get list of files changed in PR.
        
        Args:
            pr: PullRequest object
            
        Returns:
            List of File objects
        """
        return list(pr.get_files())
    
    def get_pr_diff(self, repo_full_name: str, pr_number: int) -> str:
        """Get raw diff for PR.
        
        Args:
            repo_full_name: Repository name
            pr_number: PR number
            
        Returns:
            Raw diff string
        """
        pr = self.get_pr(repo_full_name, pr_number)
        # Get diff using compare API
        repo = self.get_repo(repo_full_name)
        comparison = repo.compare(pr.base.sha, pr.head.sha)
        
        # Build diff from files
        diff_parts = []
        for file in comparison.files:
            if file.patch:
                diff_parts.append(f"diff --git a/{file.filename} b/{file.filename}")
                diff_parts.append(file.patch)
        
        return "\n\n".join(diff_parts)
    
    def create_review_comment(
        self,
        pr: PullRequest,
        commit_sha: str,
        file_path: str,
        line: int,
        body: str
    ) -> None:
        """Create inline review comment on PR.
        
        Args:
            pr: PullRequest object
            commit_sha: Commit SHA to comment on
            file_path: File path relative to repo root
            line: Line number (must be in diff)
            body: Comment text (Markdown supported)
        """
        pr.create_review_comment(
            body=body,
            commit=commit_sha,
            path=file_path,
            line=line
        )
    
    def create_pr_comment(self, pr: PullRequest, body: str) -> None:
        """Create general comment on PR (not inline).
        
        Args:
            pr: PullRequest object
            body: Comment text (Markdown)
        """
        pr.create_issue_comment(body)
    
    def create_review(
        self,
        pr: PullRequest,
        body: str,
        event: str = "COMMENT",
        comments: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Create a complete review with multiple comments.
        
        Args:
            pr: PullRequest object
            body: Overall review summary
            event: APPROVE, REQUEST_CHANGES, or COMMENT
            comments: List of review comments with format:
                {
                    "path": "file/path.py",
                    "line": 42,
                    "body": "Comment text"
                }
        """
        if comments:
            # Create review with inline comments
            pr.create_review(
                body=body,
                event=event,
                comments=comments
            )
        else:
            # Just summary comment
            pr.create_review(body=body, event=event)
    
    def get_pr_metadata(self, repo_full_name: str, pr_number: int) -> Dict[str, Any]:
        """Get comprehensive PR metadata.
        
        Args:
            repo_full_name: Repository name
            pr_number: PR number
            
        Returns:
            Dict with PR metadata
        """
        pr = self.get_pr(repo_full_name, pr_number)
        files = self.get_pr_files(pr)
        
        return {
            "number": pr.number,
            "url": pr.html_url,
            "title": pr.title,
            "description": pr.body or "",
            "author": pr.user.login,
            "base": {
                "ref": pr.base.ref,
                "sha": pr.base.sha
            },
            "head": {
                "ref": pr.head.ref,
                "sha": pr.head.sha
            },
            "state": pr.state,
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat(),
            "files_changed": [
                {
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "changes": f.changes,
                    "patch": f.patch if hasattr(f, 'patch') else None
                }
                for f in files
            ],
            "stats": {
                "total_files": len(files),
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files
            }
        }
    
    def format_review_summary(
        self,
        issues_count: int,
        critical_count: int,
        files_reviewed: int,
        processing_time: float
    ) -> str:
        """Format review summary in Markdown.
        
        Args:
            issues_count: Total issues found
            critical_count: Critical issues
            files_reviewed: Files analyzed
            processing_time: Time in seconds
            
        Returns:
            Markdown formatted summary
        """
        emoji_map = {
            0: "✅",
            1: "⚠️",
        }
        emoji = emoji_map.get(min(critical_count, 1), "🚨")
        
        summary = f"""## {emoji} Code Review Summary

**Analysis Complete**
- Files Reviewed: {files_reviewed}
- Issues Found: {issues_count}
- Critical Issues: {critical_count}
- Processing Time: {processing_time:.2f}s

Generated by AI Code Review Orchestration System
"""
        return summary
    
    def format_issue_comment(
        self,
        severity: str,
        title: str,
        description: str,
        suggestion: Optional[str] = None
    ) -> str:
        """Format individual issue comment in Markdown.
        
        Args:
            severity: Issue severity level
            title: Issue title
            description: Detailed description
            suggestion: Fix suggestion (optional)
            
        Returns:
            Markdown formatted comment
        """
        severity_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "💡",
            "low": "ℹ️",
            "info": "📝"
        }
        
        emoji = severity_emoji.get(severity.lower(), "💡")
        
        comment = f"{emoji} **{severity.upper()}**: {title}\n\n{description}"
        
        if suggestion:
            comment += f"\n\n**Suggested Fix:**\n```\n{suggestion}\n```"
        
        comment += "\n\n---\n*AI Code Review*"
        
        return comment


def test_github_api():
    """Test GitHub API connectivity and endpoints."""
    print("🔍 Testing GitHub API...")
    
    try:
        client = GitHubAPIClient()
        
        # Test 1: Rate limits
        print("\n1. Checking rate limits...")
        limits = client.check_rate_limit()
        print(f"   Core API: {limits['core']['remaining']}/{limits['core']['limit']}")
        print(f"   Search API: {limits['search']['remaining']}/{limits['search']['limit']}")
        
        # Test 2: Test repo access (if configured)
        test_repo = os.getenv("GITHUB_TEST_REPO")
        if test_repo:
            print(f"\n2. Accessing test repo: {test_repo}...")
            repo = client.get_repo(test_repo)
            print(f"   ✅ Repo: {repo.full_name}")
            print(f"   Description: {repo.description}")
            print(f"   Language: {repo.language}")
            
            # Test 3: List recent PRs
            print("\n3. Fetching recent PRs...")
            prs = list(repo.get_pulls(state='all', sort='created', direction='desc'))[:3]
            for pr in prs:
                print(f"   PR #{pr.number}: {pr.title} ({pr.state})")
            
            # Test 4: Get PR details (first PR)
            if prs:
                pr = prs[0]
                print(f"\n4. Testing PR metadata for #{pr.number}...")
                metadata = client.get_pr_metadata(test_repo, pr.number)
                print(f"   Author: {metadata['author']}")
                print(f"   Files changed: {metadata['stats']['total_files']}")
                print(f"   +{metadata['stats']['additions']} -{metadata['stats']['deletions']}")
                
                # Test 5: Format sample comments
                print("\n5. Testing comment formatting...")
                summary = client.format_review_summary(
                    issues_count=5,
                    critical_count=1,
                    files_reviewed=3,
                    processing_time=2.5
                )
                print("   Summary preview:")
                print("   " + summary.split('\n')[0])
                
                issue_comment = client.format_issue_comment(
                    severity="high",
                    title="Complex function detected",
                    description="Cyclomatic complexity exceeds threshold",
                    suggestion="Consider extracting helper methods"
                )
                print("   Issue comment preview:")
                print("   " + issue_comment.split('\n')[0])
        else:
            print("\n⚠️  GITHUB_TEST_REPO not configured - skipping repo tests")
        
        print("\n✅ GitHub API testing complete!")
        return True
        
    except GithubException as e:
        print(f"\n❌ GitHub API error: {e.status} - {e.data.get('message', 'Unknown error')}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    # Load environment
    from dotenv import load_dotenv
    load_dotenv('.env.dev')
    
    test_github_api()
