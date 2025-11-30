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


def query_trends_v1_old(repo: str, start_date: str = None, end_date: str = None) -> dict:
    """[DEPRECATED] Old version - tool calculates trend. Use query_trends() instead."""
    # This is the old implementation where tool does all calculations
    # Kept for reference, but agents should use new query_trends()
    """Analyze quality trends: improving/stable/degrading.
    
    CRITICAL UNDERSTANDING:
    We analyze FULL REPOSITORY SNAPSHOTS, not individual commit diffs!
    - Each commit has quality_score = result of running bandit+radon on ENTIRE repo at that point
    - Commit quality_score represents CUMULATIVE state of the whole codebase
    - Therefore: compare OLDEST commit (start state) vs NEWEST commit (end state)
    - NO AVERAGING NEEDED: 1 vs 1 comparison is sufficient and correct
    - Middle commits are irrelevant - they just show intermediate states
    
    Trend Calculation Strategy:
    - recent = quality_score of NEWEST commit in range (current repo state)
    - historical = quality_score of OLDEST commit in range (initial repo state)
    - delta = recent - historical (how quality changed over time)
    - trend_direction: IMPROVING (+2+), STABLE (±2), DEGRADING (-2-)
    
    Date Filtering:
    - If start_date/end_date specified: filter commits by date, then compare ends
    - If >10 commits in range: sample newest 1 + oldest 1 for efficiency
    - If no dates: use all available commits (up to 50 most recent)
    
    Args:
        repo: Repository identifier (e.g., 'facebook/react')
        start_date: Optional ISO date string (e.g., '2025-01-01') - include commits from this date
        end_date: Optional ISO date string (e.g., '2025-12-31') - include commits up to this date
    
    Returns:
        {
            "status": "success",
            "trend_direction": "IMPROVING" | "STABLE" | "DEGRADING",
            "recent_avg": 87.5,      # Quality of newest commit (current state)
            "historical_avg": 82.3,  # Quality of oldest commit (initial state)
            "delta": +5.2,
            "commits_analyzed": 50,
            "data_sample": [...]     # Sample of commits in range for context
        }
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
        
        # Determine if we need date filtering
        from datetime import datetime, timezone
        needs_date_filter = start_date or end_date
        
        if needs_date_filter:
            # When date range specified: get ALL commits in range, then sample
            # (can't use limit before filtering - would miss older commits in range)
            commits = db.query_by_repository(repo, order_by="date", descending=True)
            
            if not commits:
                return {
                    "status": "no_data",
                    "message": f"No commits found in {repo}. Database may be empty."
                }
            
            # Parse dates and make them timezone-aware (UTC) to match Firestore
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
            
            # Filter by date range
            # Strategy: If start_date given, we need:
            #   - One commit BEFORE start_date (baseline state)
            #   - Commits IN range [start_date, end_date] (evolution)
            #   - Compare: baseline vs newest in range
            
            in_range = []
            before_range = None
            
            for c in commits:
                commit_date = c.date
                
                # Skip commits after end_date
                if end_dt and commit_date > end_dt:
                    continue
                
                # If before start_date, save as baseline (take most recent one)
                if start_dt and commit_date < start_dt:
                    if before_range is None:
                        before_range = c  # Most recent commit before start_date
                    continue
                
                # Commit is in range [start_date, end_date]
                in_range.append(c)
            
            # Determine what we compare
            if start_dt and before_range:
                # Have baseline before start_date → compare it vs newest in range
                if not in_range:
                    date_range_desc = f"from {start_date}" if not end_dt else f"in range {start_date} to {end_date}"
                    return {
                        "status": "no_data",
                        "message": f"No commits found {date_range_desc}. Last commit before range was on {before_range.date.date()}."
                    }
                historical_commits = [before_range]  # State before start_date
                recent_commits = [in_range[0]]       # Newest in range (end state)
                commits = [before_range] + in_range  # For commits_analyzed count
                logger.info(f"Comparing baseline before {start_date} vs newest in range")
            else:
                # No start_date or no commits before it → use commits in range only
                commits = in_range
                if not commits:
                    return {
                        "status": "no_data",
                        "message": f"No commits found in date range {start_date or 'beginning'} to {end_date or 'now'}."
                    }
                
                # Smart sampling if too many commits
                if len(commits) > 10:
                    recent_commits = [commits[0]]   # Newest commit (end state)
                    historical_commits = [commits[-1]]  # Oldest commit (start state)
                    logger.info(f"Sampled from {len(commits)} commits: comparing start state vs end state")
                else:
                    # Use all commits, will split below
                    recent_commits = None
                    historical_commits = None
        else:
            # No date filter: just get last 50 commits (fast, good for recent trends)
            commits = db.query_by_repository(repo, limit=50, order_by="date", descending=True)
            if not commits:
                return {
                    "status": "no_data",
                    "message": f"No commits found in {repo}. Database may be empty."
                }
            recent_commits = None  # Will calculate below
            historical_commits = None
        
        # Need at least 2 commits to compare (before vs after)
        if len(commits) < 2:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 2 commits for trend analysis. Found {len(commits)} in specified range.",
                "commits_analyzed": len(commits)
            }
        
        date_range_msg = ""
        if start_date or end_date:
            date_range_msg = f" (range: {start_date or 'beginning'} to {end_date or 'now'})"
        
        logger.info(f"Analyzing trends for {repo}: {len(commits)} commits from Firestore{date_range_msg}")
        
        # Calculate trend groups if not already sampled above
        if recent_commits is None:
            # For small datasets: compare most recent vs oldest
            # Since we analyze repo snapshots (not diffs), 1 vs 1 is sufficient
            if len(commits) <= 10:
                recent_commits = [commits[0]]      # Newest = current state
                historical_commits = [commits[-1]]  # Oldest = initial state
            else:
                # Fallback (shouldn't reach here due to sampling above)
                recent_commits = [commits[0]]
                historical_commits = [commits[-1]]
        
        # Verify we have both commits to compare
        if not recent_commits or not historical_commits:
            date_context = ""
            if start_date or end_date:
                date_context = f" in range {start_date or 'beginning'} to {end_date or 'now'}"
            return {
                "status": "insufficient_data",
                "message": f"Cannot determine trend: need at least 2 commits to compare{date_context}. Found only {len(commits)} commit(s).",
                "commits_analyzed": len(commits)
            }
        
        # If same commit on both sides, cannot determine trend
        if len(recent_commits) == 1 and len(historical_commits) == 1:
            if recent_commits[0].commit_sha == historical_commits[0].commit_sha:
                return {
                    "status": "insufficient_data", 
                    "message": f"Cannot determine trend: only one unique commit found in the specified range.",
                    "commits_analyzed": 1,
                    "commit_sha": recent_commits[0].commit_sha[:7],
                    "commit_date": recent_commits[0].date.isoformat()
                }
        
        recent_scores = [c.quality_score for c in recent_commits]
        recent_avg = sum(recent_scores) / len(recent_scores)
        
        historical_scores = [c.quality_score for c in historical_commits]
        historical_avg = sum(historical_scores) / len(historical_scores)
        
        delta = recent_avg - historical_avg
        
        # Determine trend (threshold: ±2 points)
        if delta > 2.0:
            trend_direction = "IMPROVING"
        elif delta < -2.0:
            trend_direction = "DEGRADING"
        else:
            trend_direction = "STABLE"
        
        # Build data sample: include BOTH commits (oldest, newest) for comparison
        data_sample = []
        
        # Add oldest commit first (chronological order: start state)
        for commit in historical_commits:
            data_sample.append({
                "sha": commit.commit_sha[:7],
                "date": commit.date.isoformat(),
                "quality_score": round(commit.quality_score, 1),
                "total_issues": commit.total_issues,
                "author": commit.author,
                "label": "oldest"  # Mark as start state
            })
        
        # Add newest commit second (chronological order: end state)
        for commit in recent_commits:
            data_sample.append({
                "sha": commit.commit_sha[:7],
                "date": commit.date.isoformat(),
                "quality_score": round(commit.quality_score, 1),
                "total_issues": commit.total_issues,
                "author": commit.author,
                "label": "newest"  # Mark as end state
            })
        
        result = {
            "status": "success",
            "repo": repo,
            "trend_direction": trend_direction,
            "recent_avg": round(recent_avg, 1),
            "historical_avg": round(historical_avg, 1),
            "delta": round(delta, 1),
            "commits_analyzed": len(commits),
            "recent_commits": len(recent_commits),
            "historical_commits": len(historical_commits),
            "data_sample": data_sample,
            "message": f"Trend: {trend_direction} (Δ{delta:+.1f} points)"
        }
        
        # Add date range info if specified
        if start_date or end_date:
            result["date_range"] = {
                "start": start_date or "beginning",
                "end": end_date or "now"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"query_trends failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to analyze trends: {e}"
        }


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
    - Uses Firestore server-side filtering for optimal performance
    - Up to 30 files/authors use array_contains_any/IN (server-side)
    - More than 30 items fall back to client-side filtering
    - Quality/security thresholds always server-side
    
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

