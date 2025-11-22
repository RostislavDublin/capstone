"""
Repository Analyzer Tool - ADK Tool for analyzing GitHub repositories

Composite ADK tool that orchestrates:
1. Fetching commits (via github_tool)
2. Running quality audits (via AuditEngine)
3. Storing results (via RAGCorpusManager)

Pattern: Self-contained function with all backend imports inside
"""
import os
import logging

logger = logging.getLogger(__name__)


def analyze_repository(repo: str, count: int) -> dict:
    """
    Analyze recent commits from a GitHub repository for quality issues.
    
    Fetches commits, runs quality audits, and stores results in RAG corpus.
    This is the primary tool for initial repository analysis.
    
    Args:
        repo: Repository identifier (e.g., 'facebook/react')
        count: Number of recent commits to analyze (REQUIRED parameter - NO default, typical: 5-10, max: 50)
    
    Returns:
        Analysis results with quality scores and issue counts
    """
    logger.info(f"🔍 analyze_repository called with: repo={repo}, count={count}")
    
    try:
        # Backend imports go INSIDE function (not module-level)
        from tools.github_tool import list_github_commits
        from audit.engine import AuditEngine
        from storage.rag_corpus import RAGCorpusManager
        from connectors.github import GitHubConnector
        from connectors.base import CommitInfo
        from datetime import datetime
        import vertexai
        
        # Get credentials
        token = os.getenv("GITHUB_TOKEN")
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if not token or not project:
            return {
                "error": "Missing GITHUB_TOKEN or GOOGLE_CLOUD_PROJECT",
                "message": "❌ Configuration error - check environment variables"
            }
        
        # Initialize (inside function, not at module level!)
        vertexai.init(project=project, location="us-west1")
        
        # Step 1: Use GitHub tool to get commits
        commits_result = list_github_commits(repository=repo, count=count)
        if commits_result["status"] != "success":
            return {"error": commits_result["error_message"]}
        
        commits_data = commits_result["commits"]
        if not commits_data:
            return {"error": f"No commits found in {repo}"}
        
        # Step 2: Convert dict commits to CommitInfo objects for AuditEngine
        commits = []
        for c in commits_data:
            commits.append(CommitInfo(
                sha=c["sha"],
                message=c["message"],
                author=c["author"],
                author_email=c["author_email"],
                date=datetime.fromisoformat(c["date"]),
                files_changed=c["files_changed"],
                additions=c["additions"],
                deletions=c["deletions"]
            ))
        
        logger.info(f"Analyzing {len(commits)} commits from {repo}...")
        
        # Step 3: Initialize engine and storage
        connector = GitHubConnector(token=token)
        engine = AuditEngine(connector=connector)
        rag = RAGCorpusManager(corpus_name="quality-guardian-audits")
        rag.initialize_corpus()
        
        # Step 4: Analyze commits and store results
        total_issues = 0
        quality_scores = []
        
        for commit in commits:
            audit = engine.audit_commit(repo, commit)
            rag.store_commit_audit(audit)
            
            total_issues += audit.total_issues
            quality_scores.append(audit.quality_score)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "status": "success",
            "repo": repo,
            "commits_analyzed": len(commits),
            "total_issues": total_issues,
            "avg_quality_score": round(avg_quality, 1),
            "message": f"✅ Analyzed {len(commits)} commits. Avg quality: {avg_quality:.1f}/100, Issues: {total_issues}"
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {"error": str(e), "message": f"❌ Failed: {e}"}
