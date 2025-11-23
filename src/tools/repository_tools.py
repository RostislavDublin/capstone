"""Repository analysis tools for Quality Guardian agents.

Tool functions that agents use to interact with GitHub and perform audits.
Each function is self-contained with all backend imports inside.
"""
import os
import logging

logger = logging.getLogger(__name__)


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
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if not token or not project:
            return {
                "error": "Missing GITHUB_TOKEN or GOOGLE_CLOUD_PROJECT",
                "message": "Configuration error - check environment variables"
            }
        
        # Initialize
        vertexai.init(project=project, location="us-west1")
        
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
        
        # Analyze commits
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
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if not token or not project:
            return {"error": "Missing credentials"}
        
        vertexai.init(project=project, location="us-west1")
        connector = GitHubConnector(token=token)
        engine = AuditEngine(connector=connector)
        rag = RAGCorpusManager(corpus_name="quality-guardian-audits")
        rag.initialize_corpus()
        
        # Get last analyzed commit
        last_audit = rag.get_latest_audit(repo, audit_type="commit")
        last_sha = last_audit.get("commit_sha") if last_audit else None
        
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
            "message": f"Found {len(new_commits)} new commits. Avg quality: {avg_quality:.1f}/100"
        }
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {"error": str(e)}


def query_trends(repo: str, question: str) -> dict:
    """
    Query quality trends using Gemini with RAG grounding.
    
    Uses Vertex AI RAG to retrieve relevant audit history,
    then Gemini analyzes trends and provides insights.
    
    Args:
        repo: Repository identifier
        question: Question about quality trends
    
    Returns:
        AI-generated analysis based on audit history
    """
    try:
        from storage.rag_corpus import RAGCorpusManager
        from vertexai.generative_models import GenerativeModel, Tool
        from vertexai.preview import rag
        import vertexai
        
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            return {"error": "Missing GOOGLE_CLOUD_PROJECT"}
        
        vertexai.init(project=project, location="us-west1")
        rag_mgr = RAGCorpusManager(corpus_name="quality-guardian-audits")
        rag_mgr.initialize_corpus()
        
        # Build prompt for Gemini
        prompt = f"""Analyze code quality trends for {repo}.

Question: {question}

Based on commit audit data from RAG corpus, provide:
1. Trend direction (improving/stable/degrading)
2. Number of commits analyzed
3. Key findings

Be specific with numbers. Keep response concise (2-3 sentences)."""
        
        # Create RAG retrieval tool
        rag_tool = Tool.from_retrieval(
            retrieval=rag.Retrieval(
                source=rag.VertexRagStore(
                    rag_resources=[
                        rag.RagResource(
                            rag_corpus=rag_mgr._corpus_resource_name,
                        )
                    ],
                    similarity_top_k=10,
                ),
            )
        )
        
        # Gemini with RAG grounding
        model = GenerativeModel(
            model_name="gemini-2.0-flash-001",
            tools=[rag_tool],
        )
        
        response = model.generate_content(prompt)
        analysis = response.text if hasattr(response, 'text') else str(response)
        
        return {
            "status": "success",
            "question": question,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {"error": str(e)}
