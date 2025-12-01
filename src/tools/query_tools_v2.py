"""Multi-step query tools for granular trend analysis.

These tools allow agents to perform complex analysis in multiple steps:
1. filter_commits - Find commits matching criteria
2. get_commit_details - Get detailed metrics for specific commits
3. aggregate_file_metrics - Calculate file-level aggregations

This enables file-specific trend analysis and flexible workflows.
"""
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def filter_commits(
    repo: str,
    files: list = None,
    authors: list = None,
    date_from: str = None,
    date_to: str = None,
    min_quality_score: float = None,
    min_security_score: float = None,
    limit: int = 100
) -> dict:
    """Find commits matching filter criteria (Step 1 of multi-step analysis).
    
    Returns list of commit SHAs without full details for efficient filtering.
    Use get_commit_details() to fetch metrics for selected commits.
    
    Args:
        repo: Repository name (owner/repo format)
        files: Filter commits that touched these files
        authors: Filter commits by these authors
        date_from: ISO date '2024-10-01' (inclusive)
        date_to: ISO date '2024-12-31' (inclusive)
        min_quality_score: Minimum repository quality score (0-100)
        min_security_score: Minimum repository security score (0-100)
        limit: Maximum commits to return (default 100)
    
    Returns:
        {
            "status": "success",
            "commits": ["abc1234", "def5678", ...],  # 7-char SHAs
            "total_found": 15,
            "filters_applied": {...}
        }
    
    Example:
        Agent: "Find commits touching app.py in last month"
        Tool: filter_commits(repo="owner/repo", files=["app.py"], date_from="2024-11-01")
        -> Returns list of matching SHAs
    """
    try:
        from storage.firestore_client import FirestoreAuditDB
        
        db = FirestoreAuditDB()
        
        # Parse dates if provided
        date_from_dt = None
        date_to_dt = None
        if date_from:
            date_from_dt = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
        
        # Query with filters (uses client-side filtering internally)
        commits = db.query_with_filters(
            repository=repo,
            authors=authors,
            files=files,
            date_from=date_from_dt,
            date_to=date_to_dt,
            min_quality_score=min_quality_score,
            min_security_score=min_security_score,
            order_by="date",
            descending=True,
            limit=limit
        )
        
        if not commits:
            return {
                "status": "no_data",
                "message": f"No commits found matching criteria in {repo}",
                "filters_applied": {
                    "files": files,
                    "authors": authors,
                    "date_range": f"{date_from or 'beginning'} to {date_to or 'now'}",
                    "quality_threshold": min_quality_score,
                    "security_threshold": min_security_score
                }
            }
        
        # Extract SHAs and basic info
        commit_shas = [c.commit_sha[:7] for c in commits]
        
        # Build filters_applied summary
        filters_applied = {}
        if files:
            filters_applied["files"] = files
        if authors:
            filters_applied["authors"] = authors
        if date_from or date_to:
            filters_applied["date_range"] = f"{date_from or 'beginning'} to {date_to or 'now'}"
        if min_quality_score is not None:
            filters_applied["min_quality_score"] = min_quality_score
        if min_security_score is not None:
            filters_applied["min_security_score"] = min_security_score
        
        logger.info(f"filter_commits: Found {len(commit_shas)} commits in {repo}")
        
        return {
            "status": "success",
            "commits": commit_shas,
            "total_found": len(commit_shas),
            "filters_applied": filters_applied if filters_applied else None
        }
        
    except Exception as e:
        logger.error(f"filter_commits failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to filter commits: {e}"
        }


def get_commit_details(
    repo: str,
    commit_shas: list,
    scope: str = "repository",
    files: list = None
) -> dict:
    """Get detailed metrics for specific commits (Step 2 of multi-step analysis).
    
    Use after filter_commits() to fetch full details for selected commits.
    
    Args:
        repo: Repository name (owner/repo format)
        commit_shas: List of commit SHAs (7-char or full)
        scope: "repository" (repo-level metrics) or "files" (file-level metrics)
        files: If scope="files", aggregate metrics for these files only
    
    Returns:
        {
            "status": "success",
            "scope": "repository" or "files",
            "commits": [
                {
                    "sha": "abc1234",
                    "date": "2024-11-05T10:30:00Z",
                    "author": "Alice",
                    "quality_score": 85.2,  # repo or file-avg
                    "security_score": 88.5,
                    "total_issues": 5,
                    "files_analyzed": ["app.py"]  # if scope="files"
                }
            ]
        }
    
    Example:
        Agent workflow:
        1. shas = filter_commits(files=["app.py"])
        2. details = get_commit_details(commit_shas=shas, scope="files", files=["app.py"])
        -> Returns file-specific metrics for those commits
    """
    try:
        from storage.firestore_client import FirestoreAuditDB
        
        db = FirestoreAuditDB()
        
        # Fetch all commits matching SHAs
        all_commits = db.query_by_repository(repository=repo, limit=1000)
        
        # Filter to requested SHAs
        commits_map = {}
        for c in all_commits:
            short_sha = c.commit_sha[:7]
            if short_sha in commit_shas or c.commit_sha in commit_shas:
                commits_map[short_sha] = c
        
        if not commits_map:
            return {
                "status": "no_data",
                "message": f"No commits found with SHAs: {commit_shas}"
            }
        
        # Build response based on scope
        commits_data = []
        
        for sha in commit_shas:
            if sha not in commits_map:
                continue
            
            commit = commits_map[sha]
            
            if scope == "repository":
                # Return repository-level metrics
                commit_data = {
                    "sha": sha,
                    "date": commit.date.isoformat(),
                    "author": commit.author,
                    "quality_score": round(commit.quality_score, 1),
                    "security_score": round(commit.security_score, 1) if hasattr(commit, 'security_score') else None,
                    "complexity_score": round(commit.avg_complexity, 1) if hasattr(commit, 'avg_complexity') else None,
                    "total_issues": commit.total_issues,
                    "critical_issues": commit.critical_issues if hasattr(commit, 'critical_issues') else 0,
                    "high_issues": commit.high_issues if hasattr(commit, 'high_issues') else 0
                }
                
            elif scope == "files":
                # Aggregate file-level metrics (inline, no DB query)
                if not files:
                    # No files specified - return error
                    return {
                        "status": "error",
                        "message": "scope='files' requires 'files' parameter"
                    }
                
                # Check if commit has file-level data
                if not hasattr(commit, 'files') or not commit.files:
                    logger.warning(f"No file-level data for commit {sha}, using repo metrics")
                    commit_data = {
                        "sha": sha,
                        "date": commit.date.isoformat(),
                        "author": commit.author,
                        "quality_score": round(commit.quality_score, 1),
                        "security_score": round(commit.security_score, 1) if hasattr(commit, 'security_score') else None,
                        "total_issues": commit.total_issues,
                        "files_analyzed": []
                    }
                else:
                    # Filter to requested files
                    matching_files = [f for f in commit.files if f.file_path in files]
                    
                    if not matching_files:
                        continue  # Skip commits without matching files
                    
                    # Calculate averages
                    avg_quality = sum(f.quality_score for f in matching_files) / len(matching_files)
                    avg_security = sum(f.security_score for f in matching_files if hasattr(f, 'security_score')) / len(matching_files)
                    total_issues_sum = sum(f.total_issues for f in matching_files if hasattr(f, 'total_issues'))
                    
                    commit_data = {
                        "sha": sha,
                        "date": commit.date.isoformat(),
                        "author": commit.author,
                        "quality_score": round(avg_quality, 1),
                        "security_score": round(avg_security, 1),
                        "total_issues": total_issues_sum,
                        "files_analyzed": [f.file_path for f in matching_files]
                    }
            
            else:
                return {
                    "status": "error",
                    "message": f"Invalid scope: {scope}. Use 'repository' or 'files'."
                }
            
            commits_data.append(commit_data)
        
        logger.info(f"get_commit_details: Retrieved {len(commits_data)} commits with scope={scope}")
        
        return {
            "status": "success",
            "scope": scope,
            "commits": commits_data,
            "total_returned": len(commits_data)
        }
        
    except Exception as e:
        logger.error(f"get_commit_details failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to get commit details: {e}"
        }


def aggregate_file_metrics(
    repo: str,
    commit_sha: str,
    file_paths: list
) -> dict:
    """Calculate aggregated metrics for specific files in a commit (Step 3).
    
    Used internally by get_commit_details(scope="files") or can be called directly.
    
    Args:
        repo: Repository name (owner/repo format)
        commit_sha: Full or 7-char commit SHA
        file_paths: List of file paths to aggregate
    
    Returns:
        {
            "status": "success",
            "quality_score": 82.5,  # average across files
            "security_score": 85.0,  # average across files
            "total_issues": 8,  # sum across files
            "files_analyzed": ["app.py", "api.py"]
        }
    """
    try:
        from storage.firestore_client import FirestoreAuditDB
        
        db = FirestoreAuditDB()
        
        # Fetch commit
        commits = db.query_by_repository(repository=repo, limit=1000)
        commit = None
        for c in commits:
            if c.commit_sha.startswith(commit_sha) or c.commit_sha[:7] == commit_sha:
                commit = c
                break
        
        if not commit:
            return {
                "status": "no_data",
                "message": f"Commit not found: {commit_sha}"
            }
        
        # Check if commit has file-level data
        if not hasattr(commit, 'files') or not commit.files:
            # Fallback to repository-level metrics
            logger.warning(f"No file-level data for commit {commit_sha}, using repo metrics")
            return {
                "status": "success",
                "quality_score": round(commit.quality_score, 1),
                "security_score": round(commit.security_score, 1) if hasattr(commit, 'security_score') else None,
                "total_issues": commit.total_issues,
                "files_analyzed": [],
                "note": "File-level data not available, using repository-level metrics"
            }
        
        # Filter to requested files
        matching_files = [f for f in commit.files if f.file_path in file_paths]
        
        if not matching_files:
            return {
                "status": "no_data",
                "message": f"None of the requested files found in commit {commit_sha}",
                "available_files": [f.file_path for f in commit.files[:5]]
            }
        
        # Aggregate metrics
        total_quality = sum(f.quality_score for f in matching_files if hasattr(f, 'quality_score'))
        total_security = sum(f.security_score for f in matching_files if hasattr(f, 'security_score'))
        total_issues = sum(f.total_issues for f in matching_files if hasattr(f, 'total_issues'))
        
        avg_quality = total_quality / len(matching_files) if matching_files else 0
        avg_security = total_security / len(matching_files) if matching_files else 0
        
        return {
            "status": "success",
            "quality_score": round(avg_quality, 1),
            "security_score": round(avg_security, 1),
            "total_issues": total_issues,
            "files_analyzed": [f.file_path for f in matching_files]
        }
        
    except Exception as e:
        logger.error(f"aggregate_file_metrics failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to aggregate file metrics: {e}"
        }
