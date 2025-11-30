"""
Commits Checker Tool - ADK Tool for checking new commits

Finds and analyzes commits that appeared since last analysis.
Uses AuditEngine + RAGCorpusManager to detect and audit new commits.

Pattern: Self-contained function with all backend imports inside
"""
import os
import logging

logger = logging.getLogger(__name__)


def check_new_commits(repo: str) -> dict:
    """
    Check for new commits since last analysis and audit them.
    
    Compares current commits with last stored audit to find new ones.
    Use this after initial analysis to stay up-to-date.
    
    Args:
        repo: Repository identifier (e.g., 'facebook/react')
    
    Returns:
        Results for new commits found (or notification if up-to-date)
    """
    logger.info(f"🔍 check_new_commits called with: repo={repo}")
    
    try:
        # Backend imports go INSIDE function (not module-level)
        from connectors.github import GitHubConnector
        from audit.engine import AuditEngine
        from storage.rag_corpus import RAGCorpusManager
        import vertexai
        
        token = os.getenv("GITHUB_TOKEN")
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if not token or not project:
            return {
                "error": "Missing GITHUB_TOKEN or GOOGLE_CLOUD_PROJECT",
                "message": "❌ Configuration error - check environment variables"
            }
        
        # Initialize
        vertexai.init(project=project, location="us-west1")
        connector = GitHubConnector(token=token)
        engine = AuditEngine(connector=connector)
        rag = RAGCorpusManager(corpus_name="quality-guardian-audits")
        rag.initialize_corpus()
        
        # Get last analyzed commit from Firestore (deterministic storage)
        from storage.firestore_client import FirestoreAuditDB
        firestore_db = FirestoreAuditDB(project_id=project)
        last_audits = firestore_db.query_by_repository(repo, limit=1, order_by="date", descending=True)
        last_sha = last_audits[0].commit_sha if last_audits else None
        
        # Get all commits
        commits = connector.list_commits(repo)
        
        # Find new commits (stop at last analyzed)
        new_commits = []
        for commit in commits:
            if last_sha and (commit.sha == last_sha or commit.sha.startswith(last_sha)):
                break
            new_commits.append(commit)
        
        if not new_commits:
            return {
                "status": "success",
                "message": f"✅ {repo} is up-to-date (no new commits since last analysis)"
            }
        
        logger.info(f"Found {len(new_commits)} new commits in {repo}")
        
        # Analyze new commits
        total_issues = 0
        quality_scores = []
        
        for commit in new_commits:
            audit = engine.audit_commit(repo, commit)
            rag.store_commit_audit(audit)
            
            total_issues += audit.total_issues
            quality_scores.append(audit.quality_score)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "status": "success",
            "new_commits": len(new_commits),
            "total_issues": total_issues,
            "avg_quality_score": round(avg_quality, 1),
            "message": f"✅ Found {len(new_commits)} new commits. Avg quality: {avg_quality:.1f}/100, Issues: {total_issues}"
        }
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {"error": str(e), "message": f"❌ Failed: {e}"}
