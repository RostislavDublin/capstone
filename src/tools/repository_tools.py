"""Repository analysis tools for Quality Guardian agents.

Tool functions that agents use to interact with GitHub and perform audits.
Each function is self-contained with all backend imports inside.
"""
import os
import logging

logger = logging.getLogger(__name__)


def _get_rag_tool():
    """Initialize RAG corpus and return Gemini RAG tool.
    
    Shared setup for query_trends and list_analyzed_repositories.
    
    Returns:
        tuple: (rag_manager, rag_tool, stats)
    """
    import warnings
    from storage.rag_corpus import RAGCorpusManager
    from vertexai.generative_models import Tool
    from vertexai import rag
    import vertexai
    
    # Suppress deprecation warning - Vertex RAG not yet in google.genai SDK
    warnings.filterwarnings('ignore', message='.*deprecated.*', category=UserWarning)
    
    # Get project from env (PROJECT_ID works in Agent Engine, GOOGLE_CLOUD_PROJECT locally)
    project = os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise ValueError("Missing PROJECT_ID or GOOGLE_CLOUD_PROJECT")
    
    location = os.getenv("VERTEX_LOCATION", "us-west1")
    vertexai.init(project=project, location=location)
    rag_mgr = RAGCorpusManager(corpus_name="quality-guardian-audits")
    rag_mgr.initialize_corpus()
    
    # Get corpus stats
    stats = rag_mgr.get_corpus_stats()
    
    # Create RAG retrieval tool - Tool.from_retrieval is ONLY way for Vertex RAG
    rag_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=rag_mgr._corpus_resource_name,
                    )
                ],
            ),
        )
    )
    
    return rag_mgr, rag_tool, stats


def analyze_repository(repo: str, count: int = 10) -> dict:
    """
    Analyze recent commits from a GitHub repository for quality issues.
    
    Fetches commits, runs quality audits, and stores results in RAG corpus.
    This is the primary tool for initial repository analysis.
    
    Args:
        repo: Repository identifier (e.g., 'facebook/react')
        count: Number of recent commits to analyze (REQUIRED, typical: 5-10, max: 50)
    
    Returns:
        Analysis results with quality scores and issue counts
    """
    logger.info(f"🔍 analyze_repository called with: repo={repo}, count={count}")
    try:
        from tools.github_tool import list_github_commits
        from audit.engine import AuditEngine
        from storage.rag_corpus import RAGCorpusManager
        from connectors.github import GitHubConnector
        import vertexai
        
        # Get credentials
        token = os.getenv("GITHUB_TOKEN")
        project = os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if not token or not project:
            return {
                "error": "Missing GITHUB_TOKEN or GOOGLE_CLOUD_PROJECT",
                "message": "Configuration error - check environment variables"
            }
        
        # Initialize
        location = os.getenv("VERTEX_LOCATION", "us-west1")
        vertexai.init(project=project, location=location)
        
        # Use GitHub tool to get commits
        commits_result = list_github_commits(repository=repo, count=count)
        if commits_result["status"] != "success":
            return {"error": commits_result["error_message"]}
        
        commits_data = commits_result["commits"]
        if not commits_data:
            return {"error": f"No commits found in {repo}"}
        
        # Convert dict commits to CommitInfo objects for AuditEngine
        from connectors.base import CommitInfo
        from datetime import datetime
        
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
        
        # Initialize engine and storage
        connector = GitHubConnector(token=token)
        engine = AuditEngine(connector=connector)
        rag = RAGCorpusManager(corpus_name="quality-guardian-audits")
        rag.initialize_corpus()
        
        # Initialize Firestore (primary storage)
        from storage.firestore_client import FirestoreAuditDB
        firestore_db = FirestoreAuditDB(
            project_id=project,
            database=os.getenv("FIRESTORE_DATABASE", "(default)"),
            collection_prefix=os.getenv("FIRESTORE_COLLECTION_PREFIX", "quality-guardian")
        )
        
        # Analyze commits
        total_issues = 0
        quality_scores = []
        
        for commit in commits:
            audit = engine.audit_commit(repo, commit)
            
            # Primary write: Firestore (source of truth)
            try:
                firestore_db.store_commit_audit(audit)
                logger.debug(f"✓ Stored in Firestore: {commit.sha[:7]}")
            except Exception as e:
                logger.error(f"✗ Firestore write failed for {commit.sha[:7]}: {e}")
                # Don't fail - continue to RAG
            
            # Secondary write: RAG (semantic search cache, best-effort)
            try:
                display_name = f"{repo.replace('/', '_')}_commit_{commit.sha[:7]}.json"
                rag.store_commit_audit(audit, display_name=display_name)
                logger.debug(f"✓ Stored in RAG: {commit.sha[:7]}")
            except Exception as e:
                logger.warning(f"RAG write failed for {commit.sha[:7]}: {e}", exc_info=True)
                # Continue - RAG is optional cache
            
            total_issues += audit.total_issues
            quality_scores.append(audit.quality_score)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "status": "success",
            "repo": repo,
            "commits_analyzed": len(commits),
            "total_issues": total_issues,
            "avg_quality_score": round(avg_quality, 1),
            "message": f"Analyzed {len(commits)} commits. Avg quality: {avg_quality:.1f}/100, Issues: {total_issues}"
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {"error": str(e), "message": f"Failed: {e}"}


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
    try:
        from connectors.github import GitHubConnector
        from audit.engine import AuditEngine
        from storage.rag_corpus import RAGCorpusManager
        import vertexai
        
        token = os.getenv("GITHUB_TOKEN")
        project = os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if not token or not project:
            return {"error": "Missing credentials"}
        
        location = os.getenv("VERTEX_LOCATION", "us-west1")
        vertexai.init(project=project, location=location)
        connector = GitHubConnector(token=token)
        engine = AuditEngine(connector=connector)
        rag = RAGCorpusManager(corpus_name="quality-guardian-audits")
        rag.initialize_corpus()
        
        # Get last analyzed commit from Firestore (deterministic storage)
        from storage.firestore_client import FirestoreAuditDB
        firestore_db = FirestoreAuditDB(
            project_id=project,
            database=os.getenv("FIRESTORE_DATABASE", "(default)"),
            collection_prefix=os.getenv("FIRESTORE_COLLECTION_PREFIX", "quality-guardian")
        )
        last_audits = firestore_db.query_by_repository(repo, limit=1, order_by="date", descending=True)
        last_sha = last_audits[0].commit_sha if last_audits else None
        
        # Get all commits
        commits = connector.list_commits(repo)
        
        # Find new commits
        new_commits = []
        for commit in commits:
            if last_sha and (commit.sha == last_sha or commit.sha.startswith(last_sha)):
                break
            new_commits.append(commit)
        
        if not new_commits:
            return {
                "status": "success",
                "message": f"{repo} is up-to-date (no new commits)"
            }
        
        logger.info(f"Found {len(new_commits)} new commits in {repo}")
        
        # Initialize Firestore (primary storage)
        from storage.firestore_client import FirestoreAuditDB
        firestore_db = FirestoreAuditDB(
            project_id=project,
            database=os.getenv("FIRESTORE_DATABASE", "(default)"),
            collection_prefix=os.getenv("FIRESTORE_COLLECTION_PREFIX", "quality-guardian")
        )
        
        # Analyze new commits with dual write
        total_issues = 0
        quality_scores = []
        
        for commit in new_commits:
            audit = engine.audit_commit(repo, commit)
            
            # Primary write: Firestore (source of truth)
            try:
                firestore_db.store_commit_audit(audit)
                logger.debug(f"Stored in Firestore: {commit.sha[:7]}")
            except Exception as e:
                logger.error(f"Firestore write failed for {commit.sha[:7]}: {e}")
            
            # Secondary write: RAG (semantic search cache, best-effort)
            try:
                display_name = f"{repo.replace('/', '_')}_commit_{commit.sha[:7]}.json"
                rag.store_commit_audit(audit, display_name=display_name)
                logger.debug(f"Stored in RAG: {commit.sha[:7]}")
            except Exception as e:
                logger.warning(f"RAG write failed for {commit.sha[:7]}: {e}", exc_info=True)
            
            total_issues += audit.total_issues
            quality_scores.append(audit.quality_score)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "status": "success",
            "new_commits": len(new_commits),
            "total_issues": total_issues,
            "avg_quality_score": round(avg_quality, 1),
            "message": f"Found {len(new_commits)} new commits. Avg quality: {avg_quality:.1f}/100"
        }
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {"error": str(e)}


def query_trends(repo: str, question: str) -> dict:
    """
    Query quality trends using Firestore data + Gemini analysis with RAG grounding.
    
    HYBRID APPROACH (Firestore + RAG):
    - Firestore provides reliable structured data (commits, dates, scores)
    - Data passed explicitly to Gemini in prompt (no search uncertainty)
    - RAG used for semantic details (file-level issues, patterns)
    - Gemini analyzes trends with full context
    
    This ensures:
    - No "data not found" errors (Firestore is deterministic)
    - Rich semantic context (RAG for details)
    - Accurate calculations (structured data in prompt)
    
    Args:
        repo: Repository identifier
        question: Question about quality trends (natural language)
    
    Returns:
        AI-generated analysis with commit data from Firestore
    """
    try:
        import warnings
        from vertexai.generative_models import GenerativeModel
        from storage.firestore_client import FirestoreAuditDB
        import vertexai
        
        # Suppress deprecation warning - Vertex RAG not yet in google.genai
        warnings.filterwarnings('ignore', message='.*deprecated.*', category=UserWarning)
        
        # Initialize
        project = os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("VERTEX_LOCATION", "us-west1")
        vertexai.init(project=project, location=location)
        
        # Get commits from Firestore (primary source)
        db = FirestoreAuditDB(
            project_id=project,
            database=os.getenv("FIRESTORE_DATABASE", "(default)"),
            collection_prefix=os.getenv("FIRESTORE_COLLECTION_PREFIX", "quality-guardian")
        )
        
        # Check if repo exists
        repos = db.get_repositories()
        if repo not in repos:
            return {
                "status": "no_data",
                "message": f"No audit data found for {repo}. Run bootstrap or sync first."
            }
        
        # Get commits (up to 50 for analysis)
        commits = db.query_by_repository(repo, limit=50, order_by="date")
        if not commits:
            return {
                "status": "no_data",
                "message": f"No commits found in {repo}. Database may be empty."
            }
        
        logger.info(f"Querying trends for {repo}: {len(commits)} commits from Firestore")
        
        # Format commit data for prompt (most recent first)
        commits_reversed = list(reversed(commits))  # Newest first
        commit_data_str = "\n".join([
            f"{i+1}. SHA: {c.commit_sha[:7]} | Date: {c.date.isoformat()} | "
            f"Quality: {c.quality_score}/100 | Issues: {c.total_issues} | "
            f"Author: {c.author}"
            for i, c in enumerate(commits_reversed[:20])  # Show recent 20
        ])
        
        # Calculate basic stats
        recent_scores = [c.quality_score for c in commits_reversed[:5]]
        older_scores = [c.quality_score for c in commits_reversed[5:10]] if len(commits) > 5 else []
        
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        older_avg = sum(older_scores) / len(older_scores) if older_scores else recent_avg
        
        # Get RAG tool for semantic details
        _, rag_tool, _ = _get_rag_tool()
        
        # Build prompt with Firestore data + RAG grounding
        prompt = f"""You are analyzing code quality trends for repository: {repo}

COMMIT DATA (from Firestore, {len(commits)} total commits):

```
{commit_data_str}
```

STATISTICS:
- Total commits analyzed: {len(commits)}
- Recent average quality (last 5): {recent_avg:.1f}/100
- Historical average quality: {older_avg:.1f}/100
- Trend: {"IMPROVING" if recent_avg > older_avg + 2 else "DECLINING" if recent_avg < older_avg - 2 else "STABLE"}

USER QUESTION: {question}

ANALYSIS TASK:

Using the commit data above and RAG corpus for detailed issue information, analyze:

1. **Quality Trend**: Is code quality improving, declining, or stable?
2. **Issue Patterns**: What types of issues are most common?
3. **Problem Areas**: Which files/components need attention?
4. **Actionable Recommendations**: Specific actions to improve quality

OUTPUT FORMAT:

**TREND ANALYSIS**

Based on the statistics above, describe the quality trend and what's driving it.

- Issue types and frequencies (use RAG to find specific issue details)
- Problematic files or components (cite commit SHAs)
- Any patterns in authorship or timing

**RECOMMENDATIONS**

Specific, actionable steps to improve code quality, referencing commits and files where appropriate.

Use RAG corpus to get detailed information about specific issues, files, and code patterns."""
        
        # Use GenerativeModel with RAG grounding
        model = GenerativeModel(
            model_name="gemini-2.0-flash-001",
            tools=[rag_tool],
        )
        
        # Generate response with Firestore data + RAG grounding
        response = model.generate_content(prompt)
        ai_analysis = response.text if hasattr(response, 'text') else str(response)
        
        return {
            "status": "success",
            "question": question,
            "repo": repo,
            "commits_analyzed": len(commits),
            "analysis": ai_analysis,
            "message": f"Analyzed {len(commits)} commits from {repo}"
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        return {"error": str(e), "message": f"Analysis failed: {e}"}


def list_analyzed_repositories() -> dict:
    """
    List all repositories that have audit data stored.
    
    Use this when user asks:
    - "What repositories do you have?"
    - "Which repos are analyzed?"
    - "Show me all repositories"
    
    Returns:
        List of repositories with analysis stats
    """
    try:
        from storage.firestore_client import FirestoreAuditDB
        import vertexai
        
        # Get project from env (PROJECT_ID works in Agent Engine, GOOGLE_CLOUD_PROJECT locally)
        project = os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            return {"error": "Missing PROJECT_ID or GOOGLE_CLOUD_PROJECT"}
        
        location = os.getenv("VERTEX_LOCATION", "us-west1")
        vertexai.init(project=project, location=location)
        
        # Read from Firestore (primary storage)
        firestore_db = FirestoreAuditDB(
            project_id=project,
            database=os.getenv("FIRESTORE_DATABASE", "(default)"),
            collection_prefix=os.getenv("FIRESTORE_COLLECTION_PREFIX", "quality-guardian")
        )
        
        repositories = firestore_db.get_repositories()
        
        if not repositories:
            return {
                "status": "no_data",
                "message": "No repositories have been analyzed yet. Use 'analyze_repository' to start.",
                "repositories": [],
                "total_repositories": 0
            }
        
        # Get stats for each repository from Firestore
        repo_stats = []
        total_commits = 0
        for repo in repositories:
            stats = firestore_db.get_repository_stats(repo)
            if stats:
                total_commits += stats["total_commits"]
                repo_stats.append({
                    "repository": repo,
                    "total_commits": stats["total_commits"],
                    "last_analyzed": stats["last_analyzed"].isoformat() if stats.get("last_analyzed") else None
                })
        
        return {
            "status": "success",
            "repositories": repo_stats,
            "total_repositories": len(repositories),
            "total_commits": total_commits,
            "message": f"Found {len(repositories)} analyzed repositories with {total_commits} total commits"
        }
        
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}", exc_info=True)
        return {"error": str(e), "message": f"Could not list repositories: {e}"}
