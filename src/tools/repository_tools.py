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
    from storage.rag_corpus import RAGCorpusManager
    from vertexai.generative_models import Tool
    from vertexai.preview import rag
    import vertexai
    
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise ValueError("Missing GOOGLE_CLOUD_PROJECT")
    
    vertexai.init(project=project, location="us-west1")
    rag_mgr = RAGCorpusManager(corpus_name="quality-guardian-audits")
    rag_mgr.initialize_corpus()
    
    # Get corpus stats
    stats = rag_mgr.get_corpus_stats()
    
    # Create RAG retrieval tool
    rag_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=rag_mgr._corpus_resource_name,
                    )
                ],
                similarity_top_k=50,  # More results for better coverage
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
        
        # Initialize Firestore (primary storage)
        from storage.firestore_client import FirestoreAuditDB
        firestore_db = FirestoreAuditDB(
            project_id=project,
            database="(default)",
            collection_prefix="quality-guardian"
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
        
        # Initialize Firestore (primary storage)
        from storage.firestore_client import FirestoreAuditDB
        firestore_db = FirestoreAuditDB(
            project_id=project,
            database="(default)",
            collection_prefix="quality-guardian"
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
    Query quality trends using Gemini with RAG grounding (ADK Memory pattern).
    
    CORRECT APPROACH (per ADK Memory docs):
    - RAG provides semantic search over stored audit history
    - Gemini analyzes trends using RAG-grounded context
    - No manual JSON parsing - let RAG + Gemini do the work
    
    This pattern mirrors ADK's Memory system:
    - Store: commit audits saved to RAG corpus
    - Retrieve: semantic search finds relevant audits  
    - Analyze: Gemini extracts insights with RAG grounding
    
    Args:
        repo: Repository identifier
        question: Question about quality trends (natural language)
    
    Returns:
        AI-generated analysis with corpus stats
    """
    try:
        from vertexai.generative_models import GenerativeModel
        
        # Get RAG setup (shared with list_analyzed_repositories)
        _, rag_tool, stats = _get_rag_tool()
        
        if stats.get("commit_files", 0) == 0:
            return {
                "status": "no_data",
                "message": f"No audit data found for {repo}. Run bootstrap or sync first.",
                "corpus_stats": stats
            }
        
        logger.info(f"Querying trends for {repo}: {stats['commit_files']} commits in corpus")
        
        # Build comprehensive prompt with data extraction instructions
        prompt = f"""You are analyzing code quality trends for repository: {repo}

CORPUS INFORMATION:
- Total commit audits stored: {stats['commit_files']}
- Repository: {repo}

USER QUESTION: {question}

STEP-BY-STEP ANALYSIS ALGORITHM:

STEP 1: DATA EXTRACTION
From the RAG corpus commit audit data, extract for EACH commit:
- commit_sha (string)
- date (ISO format timestamp)
- quality_score (0-100 float)
- total_issues (integer)
- critical_issues (integer)
- security_issues (list/count)
- complexity_issues (list/count)
- author (string)
- files (list of changed files with their issues)

STEP 2: TEMPORAL ORDERING
Sort commits by date (newest first). Identify:
- Recent commits: last 3-5 commits
- Historical commits: older commits for comparison

STEP 3: TREND CALCULATION
Calculate trend direction using this algorithm:
```
recent_avg_quality = average(quality_score of last 3-5 commits)
historical_avg_quality = average(quality_score of all older commits)
trend_delta = recent_avg_quality - historical_avg_quality

if trend_delta > 5: trend = "IMPROVING"
elif trend_delta < -5: trend = "DEGRADING"
else: trend = "STABLE"
```

STEP 4: PATTERN DETECTION
Analyze the extracted data to find:
- Most frequent security issue types (e.g., "SQL injection", "hardcoded password")
- Most frequent complexity issues (high complexity functions)
- Files that appear in multiple commits with issues (hotspots)
- Authors with highest/lowest average quality scores

STEP 5: ACTIONABLE INSIGHTS
Based on patterns, recommend:
- Which critical issues to fix first (cite specific commits/files)
- Which files need refactoring (most problematic)
- What coding practices to improve

===== MANDATORY OUTPUT FORMAT (FOLLOW EXACTLY) =====

YOU MUST START WITH THIS SECTION - NO EXCEPTIONS:

**📊 DATA SAMPLE (PROOF OF GROUNDING)**

Extract commit data from RAG corpus and list here. Example format:

```
Recent Commits (last 3, newest first):
1. SHA: b751439 | Date: 2024-11-22T15:30 | Quality: 89.5/100 | Issues: 3 | Author: John Doe
2. SHA: a7454cf | Date: 2024-11-22T14:20 | Quality: 87.3/100 | Issues: 5 | Author: Jane Smith  
3. SHA: 8439d23 | Date: 2024-11-22T13:10 | Quality: 86.1/100 | Issues: 4 | Author: John Doe

Historical Commits (older, for baseline):
1. SHA: 65cdf3b | Date: 2024-11-21T10:00 | Quality: 92.0/100 | Issues: 2 | Author: Jane Smith
2. SHA: 20c7b25 | Date: 2024-11-20T09:00 | Quality: 88.5/100 | Issues: 3 | Author: Bob Wilson
```

⚠️ CRITICAL RULES:
- Use ACTUAL commit SHAs from RAG (not invented examples)
- Extract REAL dates, scores, issue counts from audit data
- If RAG has fewer commits, list what's available
- DO NOT proceed without this section

---

**📈 TREND ANALYSIS** (calculated from data above)

Show your calculation explicitly:

```
Recent avg = (89.5 + 87.3 + 86.1) / 3 = 87.6
Historical avg = (92.0 + 88.5) / 2 = 90.25
Delta = 87.6 - 90.25 = -2.65

Trend: DEGRADING (recent < historical)
```

Replace with your actual calculations from the commits you listed above.

**Key Metrics**:
- Commits analyzed: [number] (must match data sample above)
- Current quality: [latest commit score from sample]
- Critical issues: [count across all commits]
- Security issues: [count]
- Complexity issues: [count]

**Issue Patterns** (with commit references):
1. [Most common issue type]: [count] occurrences in commits: [SHA1, SHA2, ...]
2. [Second most common]: [count] occurrences in commits: [SHA1, SHA2, ...]
3. [Third most common]: [count] occurrences in commits: [SHA1, SHA2, ...]

**Problematic Files** (with commit evidence):
- [file path]: [issue count] in commits [SHA1, SHA2], quality: [score]
- [file path]: [issue count] in commits [SHA1, SHA2], quality: [score]

**Actionable Recommendations**:
1. [Specific action with commit SHA/file/line reference from data above]
2. [Specific action with commit SHA/file/line reference from data above]
3. [Specific action with commit SHA/file/line reference from data above]

CRITICAL REQUIREMENTS:
1. You MUST list actual commit SHAs with their data (not placeholders)
2. All numbers MUST be calculated from the commits you listed
3. Show your calculation for trend (e.g., "(89.5 + 87.3 + 86.1) / 3 = 87.6")
4. Every recommendation MUST cite a specific commit SHA from your data sample
5. Do NOT invent data - extract it from RAG corpus only"""
        
        # Use RAG tool from shared setup (Gemini with RAG grounding)
        model = GenerativeModel(
            model_name="gemini-2.0-flash-001",
            tools=[rag_tool],
        )
        
        # Generate response with RAG-grounded context
        response = model.generate_content(prompt)
        ai_analysis = response.text if hasattr(response, 'text') else str(response)
        
        return {
            "status": "success",
            "question": question,
            "repo": repo,
            "commits_in_corpus": stats["commit_files"],
            "analysis": ai_analysis,
            "corpus_stats": stats,
            "message": f"Analyzed {stats['commit_files']} commits from {repo}"
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
        
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            return {"error": "Missing GOOGLE_CLOUD_PROJECT"}
        
        vertexai.init(project=project, location="us-west1")
        
        # Read from Firestore (primary storage)
        firestore_db = FirestoreAuditDB(
            project_id=project,
            database="(default)",
            collection_prefix="quality-guardian"
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
