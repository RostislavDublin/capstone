"""GitHub tool for ADK agents - declarative interface to GitHub API.

This module provides ADK-compatible tool functions for GitHub operations.
Each function follows ADK tool patterns:
- Clear docstring with Args/Returns for LLM to understand
- Simple parameters that LLM can construct
- Dictionary returns (JSON-serializable)
- All logic self-contained within function
"""

import os
from typing import List, Optional


def list_github_commits(
    repository: str,
    count: int = 10,
    branch: Optional[str] = None,
    skip: int = 0
) -> dict:
    """
    List recent commits from a GitHub repository.
    
    Use this tool when you need to:
    - Get recent commit history from a repository
    - Analyze what changes were made
    - See who authored commits and when
    
    Args:
        repository: Repository identifier in format "owner/repo" 
                   (e.g., "facebook/react" or "microsoft/vscode")
        count: Number of recent commits to return (default: 10, max: 100)
        branch: Branch name to get commits from (default: repository's main branch)
        skip: Number of most recent commits to skip (default: 0)
              Use this to get older commits, leaving newer ones for later sync
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - commits: List of commit objects with sha, message, author, date, files
            - error_message: Error description (only if status="error")
    
    Example usage:
        To analyze recent changes: list_github_commits("owner/repo", count=5)
        To get older commits: list_github_commits("owner/repo", count=5, skip=3)
        To check specific branch: list_github_commits("owner/repo", branch="develop")
    """
    try:
        from github import Auth, Github
        
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {
                "status": "error",
                "error_message": "GITHUB_TOKEN environment variable not set"
            }
        
        # Initialize GitHub client
        auth = Auth.Token(token)
        client = Github(auth=auth)
        repo = client.get_repo(repository)
        
        # Get commits from specified branch or default
        sha = branch if branch else repo.default_branch
        commits_iter = repo.get_commits(sha=sha)
        
        # Collect commit data
        commits = []
        for i, commit in enumerate(commits_iter):
            if i >= count:
                break
            
            files = commit.files if commit.files else []
            commits.append({
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": commit.commit.author.name,
                "author_email": commit.commit.author.email,
                "date": commit.commit.author.date.isoformat(),
                "files_changed": [f.filename for f in files],
                "additions": commit.stats.additions,
                "deletions": commit.stats.deletions,
            })
        
        return {
            "status": "success",
            "repository": repository,
            "branch": sha,
            "commits": commits,
            "count": len(commits)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to fetch commits: {str(e)}"
        }


def get_github_repository_info(repository: str) -> dict:
    """
    Get metadata and information about a GitHub repository.
    
    Use this tool when you need to:
    - Learn about a repository (description, language, topics)
    - Get repository statistics
    - Find the default branch name
    
    Args:
        repository: Repository identifier in format "owner/repo"
                   (e.g., "torvalds/linux" or "python/cpython")
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - info: Repository metadata (name, owner, description, language, stars, etc)
            - error_message: Error description (only if status="error")
    
    Example usage:
        To learn about a repo: get_github_repository_info("owner/repo")
    """
    try:
        from github import Auth, Github
        
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {
                "status": "error",
                "error_message": "GITHUB_TOKEN environment variable not set"
            }
        
        auth = Auth.Token(token)
        client = Github(auth=auth)
        repo = client.get_repo(repository)
        
        return {
            "status": "success",
            "info": {
                "full_name": repo.full_name,
                "owner": repo.owner.login,
                "name": repo.name,
                "description": repo.description,
                "language": repo.language,
                "default_branch": repo.default_branch,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "topics": repo.get_topics(),
                "created_at": repo.created_at.isoformat(),
                "homepage": repo.homepage,
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to fetch repository info: {str(e)}"
        }


def get_github_commit_diff(repository: str, commit_sha: str) -> dict:
    """
    Get the full diff (code changes) for a specific GitHub commit.
    
    Use this tool when you need to:
    - See exactly what code changed in a commit
    - Analyze the details of modifications
    - Review additions and deletions line-by-line
    
    Args:
        repository: Repository identifier in format "owner/repo"
        commit_sha: The commit SHA hash (can be full or abbreviated)
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - diff: Unified diff text showing all changes
            - error_message: Error description (only if status="error")
    
    Example usage:
        To review commit changes: get_github_commit_diff("owner/repo", "abc123")
    """
    try:
        import requests
        from github import Auth, Github
        
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {
                "status": "error",
                "error_message": "GITHUB_TOKEN environment variable not set"
            }
        
        # Use raw GitHub API for diff (PyGithub doesn't support this)
        response = requests.get(
            f"https://api.github.com/repos/{repository}/commits/{commit_sha}",
            headers={
                "Accept": "application/vnd.github.v3.diff",
                "Authorization": f"token {token}",
            },
        )
        response.raise_for_status()
        
        return {
            "status": "success",
            "repository": repository,
            "commit_sha": commit_sha,
            "diff": response.text
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to fetch commit diff: {str(e)}"
        }
