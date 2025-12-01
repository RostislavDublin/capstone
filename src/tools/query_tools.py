"""Query tools for specialized analytics.

Each tool focuses on one type of analysis using Firestore as primary data source.
RAG is used only for semantic details (examples, code context).
"""
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def _select_audit_sample(commits: list, start_date_str: str = None, 
                         end_date_str: str = None, max_points: int = 20) -> list:
    """
    Select up to max_points commits for trend analysis using time-based sampling.
    
    Key logic:
    - Divide time period into max_points intervals
    - For each interval: take LAST commit BEFORE interval start (snapshot logic)
    - If no commit in interval → use previous commit (forward-fill)
    - First point always BEFORE start_date (baseline state)
    
    Args:
        commits: List sorted newest to oldest
        start_date_str: ISO date '2025-10-25' (analysis starts here)
        end_date_str: ISO date '2025-11-30' (analysis ends here)
        max_points: Max commits to return (default 20)
    
    Returns:
        List of commits in CHRONOLOGICAL order (oldest first)
    """
    if not commits:
        return []
    
    # If few commits, return all in chronological order
    if len(commits) <= max_points:
        return list(reversed(commits))
    
    # Determine time range
    if start_date_str:
        start_dt = datetime.fromisoformat(start_date_str).replace(tzinfo=timezone.utc)
        # Baseline: one day before start (to capture "before" state)
        baseline_dt = start_dt - timedelta(days=1)
    else:
        # No start date → use oldest commit as baseline
        baseline_dt = commits[-1].date
    
    if end_date_str:
        end_dt = datetime.fromisoformat(end_date_str).replace(tzinfo=timezone.utc)
    else:
        # No end date → use newest commit
        end_dt = commits[0].date
    
    # Create time points
    total_duration = (end_dt - baseline_dt).total_seconds()
    if total_duration <= 0:
        # Edge case: single point in time
        return [commits[0]]
    
    interval = total_duration / (max_points - 1)  # -1 to include both endpoints
    
    time_points = []
    for i in range(max_points):
        point = baseline_dt + timedelta(seconds=i * interval)
        time_points.append(point)
    
    # For each time point, find last commit BEFORE or AT that point
    selected = []
    last_commit = None
    
    for time_point in time_points:
        # Find commits at or before this time point (sorted newest to oldest)
        candidates = [c for c in commits if c.date <= time_point]
        
        if candidates:
            # Take most recent (first in list)
            commit = candidates[0]
            last_commit = commit
        elif last_commit:
            # No commit at this point → forward-fill from previous
            commit = last_commit
        else:
            # No commits before this point yet → skip
            continue
        
        # Avoid consecutive duplicates
        if not selected or selected[-1].commit_sha != commit.commit_sha:
            selected.append(commit)
    
    return selected  # Already in chronological order


def query_trends(
    repo: str, 
    start_date: str = None, 
    end_date: str = None,
    files: list = None,
    authors: list = None,
    min_quality_score: float = None,
    min_security_score: float = None
) -> dict:
    """Fetch audit sample for intelligent trend analysis by agent with advanced filtering.
    
    NEW APPROACH (v2 - Smart Agent):
    - Tool returns RAW DATA (up to 20 audit snapshots)
    - Agent does INTERPRETATION (trend, pattern, insights)
    - Allows flexible, context-aware analysis by LLM
    
    CRITICAL UNDERSTANDING:
    Each commit quality_score = FULL REPO SNAPSHOT analysis (bandit+radon on entire codebase).
    Not individual commit diffs!
    
    Sampling Strategy:
    - Divide time period into up to 20 intervals
    - For each interval: take last commit BEFORE interval start (snapshot at that moment)
    - If start_date specified: first sample is BEFORE start_date (baseline state)
    - Forward-fill if no commits in some intervals
    
    Filtering (NEW):
    - Date ranges and score thresholds use server-side filtering (fast)
    - Files and authors use client-side filtering (avoids Firestore index requirement)
    - Efficient for <10K commits without manual index creation
    - Filter happens before sampling (minimal overhead)
    
    Args:
        repo: Repository name (owner/repo format)
        start_date: Optional ISO date '2025-01-01' (analyze from this date)
        end_date: Optional ISO date '2025-12-31' (analyze up to this date)
        files: Optional list of file paths to filter by (e.g., ["src/api.py", "src/auth.py"])
        authors: Optional list of commit authors to filter by (e.g., ["Alice", "Bob"])
        min_quality_score: Optional minimum quality score threshold (0-100)
        min_security_score: Optional minimum security score threshold (0-100)
    
    Returns:
        {
            "status": "success",
            "repo": "owner/repo",
            "sample": [
                {
                    "sha": "abc1234",
                    "date": "2025-10-25T10:30:00Z",
                    "quality_score": 82.6,
                    "security_score": 85.0,
                    "complexity_score": 5.2,  # avg_complexity
                    "total_issues": 8,
                    "critical_issues": 0,
                    "high_issues": 2,
                    "medium_issues": 4,
                    "low_issues": 2,
                    "author": "Alice",
                    "label": "baseline" | "in_range" | "oldest" | "newest",
                    "files_in_scope": 2  # Only if files filter was used
                },
                ...  # up to 20 commits
            ],
            "period": {
                "start": "2025-10-24",  # baseline date (before start_date if specified)
                "end": "2025-11-30",
                "days": 37
            },
            "total_commits_in_db": 45,
            "sample_size": 15,
            "filters_applied": {
                "files": ["src/api.py"],  # If filters were used
                "authors": ["Alice", "Bob"],
                "min_quality_score": 75.0
            }
        }
        
        Note: security_issues and complexity_issues arrays are NOT included 
        to save token capacity. Agent analyzes aggregate metrics only.
    """
    try:
        from storage.firestore_client import FirestoreAuditDB
        
        # Initialize Firestore
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            return {"error": "Missing GOOGLE_CLOUD_PROJECT"}
        
        db = FirestoreAuditDB(
            project_id=project,
            database="(default)",
            collection_prefix="quality-guardian"
        )
        
        # Check if repo exists
        repos = db.get_repositories()
        if repo not in repos:
            return {
                "status": "no_data",
                "message": f"No audit data found for {repo}. Run bootstrap or sync first."
            }
        
        # Parse dates if provided
        date_from_dt = None
        date_to_dt = None
        if start_date:
            date_from_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        if end_date:
            date_to_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        
        # Get commits with advanced filtering
        # Use query_with_filters for server-side optimization
        commits = db.query_with_filters(
            repository=repo,
            authors=authors,
            files=files,
            date_from=date_from_dt,
            date_to=date_to_dt,
            min_quality_score=min_quality_score,
            min_security_score=min_security_score,
            order_by="date",
            descending=True
        )
        
        if not commits:
            return {
                "status": "no_data",
                "message": f"No commits found in {repo}. Database may be empty."
            }
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        if end_date:
            end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        
        # Filter commits by date range (keep commits in range + one before for baseline)
        if start_dt or end_dt:
            filtered = []
            baseline = None
            
            for c in commits:
                # Keep one commit before start_date as baseline
                if start_dt and c.date < start_dt:
                    if baseline is None:
                        baseline = c
                    continue
                
                # Skip commits after end_date
                if end_dt and c.date > end_dt:
                    continue
                
                filtered.append(c)
            
            # Add baseline to beginning
            if baseline:
                filtered.append(baseline)
            
            commits = filtered
        
        if not commits:
            date_desc = f"in range {start_date or 'beginning'} to {end_date or 'now'}"
            return {
                "status": "no_data",
                "message": f"No commits found {date_desc}."
            }
        
        if len(commits) < 2:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 2 commits for trend analysis. Found {len(commits)}.",
                "commits_analyzed": len(commits)
            }
        
        # Select sample using smart time-based sampling
        sample_commits = _select_audit_sample(commits, start_date, end_date, max_points=20)
        
        # Build sample data for agent
        sample = []
        for i, commit in enumerate(sample_commits):
            # Determine label
            if i == 0:
                label = "baseline" if start_date else "oldest"
            elif i == len(sample_commits) - 1:
                label = "newest"
            else:
                label = "in_range"
            
            # Include only aggregate metrics (no detail arrays for token efficiency)
            sample_data = {
                "sha": commit.commit_sha[:7],
                "date": commit.date.isoformat(),
                "quality_score": round(commit.quality_score, 1),
                "security_score": round(commit.security_score, 1) if hasattr(commit, 'security_score') else None,
                "complexity_score": round(commit.avg_complexity, 1) if hasattr(commit, 'avg_complexity') else None,
                "total_issues": commit.total_issues,
                "critical_issues": commit.critical_issues if hasattr(commit, 'critical_issues') else 0,
                "high_issues": commit.high_issues if hasattr(commit, 'high_issues') else 0,
                "medium_issues": commit.medium_issues if hasattr(commit, 'medium_issues') else 0,
                "low_issues": commit.low_issues if hasattr(commit, 'low_issues') else 0,
                "author": commit.author,
                "label": label
            }
            
            # Add file count if file filtering was used
            if files:
                sample_data["files_in_scope"] = len([f for f in commit.files_changed if f in files])
            
            sample.append(sample_data)
        
        # Calculate period info
        period_start = sample[0]["date"][:10]  # ISO date only
        period_end = sample[-1]["date"][:10]
        
        period_start_dt = datetime.fromisoformat(sample[0]["date"])
        period_end_dt = datetime.fromisoformat(sample[-1]["date"])
        days = (period_end_dt - period_start_dt).days
        
        result = {
            "status": "success",
            "repo": repo,
            "sample": sample,
            "period": {
                "start": period_start,
                "end": period_end,
                "days": days
            },
            "total_commits_in_db": len(commits),
            "sample_size": len(sample)
        }
        
        # Add filters_applied for transparency
        filters_applied = {}
        if files:
            filters_applied["files"] = files
        if authors:
            filters_applied["authors"] = authors
        if min_quality_score is not None:
            filters_applied["min_quality_score"] = min_quality_score
        if min_security_score is not None:
            filters_applied["min_security_score"] = min_security_score
        
        if filters_applied:
            result["filters_applied"] = filters_applied
        
        logger.info(f"Trend analysis sample for {repo}: {len(sample)} commits over {days} days")
        
        return result
        
    except Exception as e:
        logger.error(f"query_trends failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to fetch trend data: {e}"
        }

