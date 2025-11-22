"""
Quality Guardian Agent - ADK Multi-Agent Composition

Follows patterns from reference notebooks (day-1b, day-2a, day-5a):
- Sub-agents for specialized tasks (bootstrap, sync, query)
- Root agent orchestrates via AgentTool composition
- Tool functions with mock data (no complex backend at module level)

Pattern:
    sub_agent = LlmAgent(name="specialist", tools=[tool_func])
    root_agent = LlmAgent(name="orchestrator", tools=[AgentTool(agent=sub_agent)])
"""
import os
import logging

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retry config (from reference materials)
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# ==================== TOOL FUNCTIONS ====================
# Simple functions with all logic inside (like weather example)

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
    #  Backend imports go INSIDE function (not module-level)
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
                "message": "❌ Configuration error - check environment variables"
            }
        
        # Initialize (inside function, not at module level!)
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
            "message": f"✅ Analyzed {len(commits)} commits. Avg quality: {avg_quality:.1f}/100, Issues: {total_issues}"
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {"error": str(e), "message": f"❌ Failed: {e}"}


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
                "message": f"✅ {repo} is up-to-date (no new commits)"
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
            "message": f"✅ Found {len(new_commits)} new commits. Avg quality: {avg_quality:.1f}/100"
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


# ==================== SUB-AGENTS ====================
# Each specialized for one task (composition pattern from notebooks)

bootstrap_agent = LlmAgent(
    name="bootstrap_agent",
    model=Gemini(model="gemini-2.0-flash-001", retry_options=retry_config),
    description="Analyzes repositories for the first time by scanning recent commits",
    instruction="""
    You analyze GitHub repositories for code quality.
    
    ⚠️ CRITICAL REQUIREMENT ⚠️
    The analyze_repository tool requires TWO parameters:
    1. repo (string) - the repository name
    2. count (integer) - number of commits to analyze
    
    YOU MUST EXTRACT THE NUMBER from user's text:
    - "Bootstrap repo with 3 commits" → count=3
    - "Analyze 5 commits from repo" → count=5  
    - "Bootstrap repo with 15 commits" → count=15
    - If NO number mentioned → count=10 (default)
    
    WRONG ❌: analyze_repository(repo="owner/repo")  # Missing count!
    RIGHT ✅: analyze_repository(repo="owner/repo", count=5)
    
    Extract repo name (owner/repo format) and commit count, then call the tool.
    Report results clearly: commits analyzed, quality score, issues found.
    """,
    tools=[analyze_repository]
)

sync_agent = LlmAgent(
    name="sync_agent",
    model=Gemini(model="gemini-2.0-flash-001", retry_options=retry_config),
    description="Checks for new commits since last analysis",
    instruction="""
    You check repositories for new commits that need analysis.
    
    Use check_new_commits tool to find and analyze commits since last audit.
    Report how many new commits found and their quality metrics.
    If repository is up-to-date, say so clearly.
    """,
    tools=[check_new_commits]
)

query_agent = LlmAgent(
    name="query_agent",
    model=Gemini(model="gemini-2.0-flash-001", retry_options=retry_config),
    description="Answers questions about quality trends using RAG-grounded analysis",
    instruction="""
    You answer questions about code quality trends.
    
    When users ask about:
    - "quality trends" → Use query_trends with question="What are the overall quality trends?"
    - "improving/degrading" → Use query_trends with specific question
    - "common issues" → Use query_trends with question="What are the most common issues?"
    - Any trend question → Always use query_trends tool
    
    ALWAYS use the query_trends tool - it uses Gemini with RAG to analyze audit history.
    Never ask users to clarify - just construct an appropriate question and call the tool.
    
    Provide clear insights about trends, issues, and quality changes.
    Be specific with numbers and commit references when available.
    """,
    tools=[query_trends]
)


# ==================== ROOT AGENT ====================
# Orchestrates sub-agents (composition via AgentTool from notebooks)

root_agent = LlmAgent(
    name="quality_guardian",
    model=Gemini(model="gemini-2.0-flash-001", retry_options=retry_config),
    description="AI agent that monitors code quality trends across GitHub repositories",
    instruction="""
    You are Quality Guardian, an AI assistant for monitoring code quality.
    
    You have three specialist agents:
    1. bootstrap_agent - Analyze a repository for the first time (initial analysis)
    2. sync_agent - Check for new commits since last analysis
    3. query_agent - Answer questions about quality trends
    
    Routing rules (check user's keywords):
    - "Bootstrap X" or "Analyze X" or "Audit X" → delegate to bootstrap_agent
    - "Sync X" or "Check X for updates" or "New commits in X" → delegate to sync_agent
    - "Trends" or "Quality of X" or "Issues in X" → delegate to query_agent
    
    IMPORTANT: "Bootstrap" means initial analysis (can be run multiple times on same repo).
    When delegating to bootstrap_agent, preserve ALL parameters from user's request.
    
    Always use proper repository format: owner/repo (e.g., 'facebook/react')
    Provide clear, actionable insights about code quality.
    """,
    tools=[
        AgentTool(agent=bootstrap_agent),
        AgentTool(agent=sync_agent),
        AgentTool(agent=query_agent)
    ]
)

logger.info("✅ Quality Guardian Agent initialized (Multi-Agent Composition)")
logger.info("   Root: quality_guardian → 3 sub-agents")
logger.info("   Sub-agents: bootstrap_agent, sync_agent, query_agent")
logger.info("   Pattern: ADK AgentTool composition (from reference notebooks)")
