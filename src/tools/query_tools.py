"""Query tools for specialized analytics.

Each tool focuses on one type of analysis using Firestore as primary data source.
RAG is used only for semantic details (examples, code context).
"""
import os
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def query_trends(repo: str, start_date: str = None, end_date: str = None) -> dict:
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
