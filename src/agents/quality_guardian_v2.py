"""Quality Guardian Agent v2 - Agent with natural language interface.

Implementation using Vertex AI Gemini for command parsing and orchestration.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from audit.engine import AuditEngine
from connectors.github import GitHubConnector
from handlers.bootstrap import BootstrapHandler
from storage.rag_corpus import RAGCorpusManager

logger = logging.getLogger(__name__)


class QualityGuardianAgentV2:
    """ADK Agent for Quality Guardian - natural language command interface.
    
    Accepts natural language commands and orchestrates backend tools:
    - "Bootstrap facebook/react using tags from 2024"
    - "Sync myorg/myrepo to get latest commits"
    - "Show security trends for myorg/myrepo in Q3 2024"
    
    Uses Gemini 2.0 Flash for command parsing and tool orchestration.
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        google_project: Optional[str] = None,
        vertex_location: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-001",
    ):
        """Initialize Quality Guardian Agent.
        
        Args:
            github_token: GitHub API token (or GITHUB_TOKEN env var)
            google_project: GCP project ID (or GOOGLE_CLOUD_PROJECT)
            vertex_location: Vertex AI location (or VERTEX_LOCATION)
            model_name: Gemini model for orchestration (Vertex AI stable version)
        """
        # Get credentials
        self.github_token = github_token or os.getenv("GITHUB_TOKEN", "")
        self.google_project = google_project or os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.vertex_location = vertex_location or os.getenv("VERTEX_LOCATION", "us-west1")
        
        if not self.github_token:
            raise ValueError("GitHub token required (GITHUB_TOKEN env var or parameter)")
        
        # Initialize backend components
        self.connector = GitHubConnector(token=self.github_token)
        self.audit_engine = AuditEngine(connector=self.connector)
        self.bootstrap_handler = BootstrapHandler(self.connector, self.audit_engine)
        
        # Initialize RAG Corpus (needs vertexai.init first)
        import vertexai
        vertexai.init(project=self.google_project, location=self.vertex_location)
        self.rag_manager = RAGCorpusManager(corpus_name="quality-guardian-audits")
        
        # Initialize or get existing corpus
        # NOTE: This will create a NEW corpus if it doesn't exist
        try:
            corpus_name = self.rag_manager.initialize_corpus()
            logger.info(f"RAG Corpus ready: {corpus_name}")
        except Exception as e:
            logger.error(f"RAG Corpus initialization failed: {e}")
            raise
        
        # Store model name for Vertex AI calls
        self.model_name = model_name
        
        logger.info("✅ Quality Guardian Agent initialized")
        logger.info(f"   Model: {model_name} (Vertex AI)")
        logger.info(f"   GitHub: {self.connector}")
        logger.info(f"   RAG: {google_project} ({vertex_location})")
    
    # ==================== TOOL FUNCTIONS ====================
    # These are exposed to Gemini Agent for orchestration
    
    def bootstrap_repository(
        self,
        repo_identifier: str,
        strategy: str = "recent",
        count: int = 10,
        time_range_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Bootstrap a repository with historical commit analysis.
        
        This tool scans historical commits and stores audits in RAG.
        
        Args:
            repo_identifier: Repository in format 'owner/repo' (e.g., 'facebook/react')
            strategy: Sampling strategy - 'recent' (latest commits), 'tags' (version tags), 
                     'weekly' (one per week), 'monthly' (one per month)
            count: Number of commits to analyze (for 'recent' strategy)
            time_range_days: Optional time range in days (e.g., 180 for last 6 months)
        
        Returns:
            dict with status, commits_analyzed, quality_score, issues_found
        """
        try:
            logger.info(f"🚀 Bootstrap: {repo_identifier} (strategy={strategy}, count={count})")
            
            # Get repository info
            repo_info = self.connector.get_repository_info(repo_identifier)
            
            # Calculate date range
            date_start = None
            if time_range_days:
                from datetime import timedelta
                date_start = datetime.now() - timedelta(days=time_range_days)
            
            # Get commits based on strategy
            if strategy == "tags":
                # Get tagged releases
                # TODO: Implement tag-based sampling
                commits = self.connector.list_commits(repo_identifier, branch=repo_info.default_branch)[:count]
            else:
                # Default: get recent commits
                commits = self.connector.list_commits(repo_identifier, branch=repo_info.default_branch)[:count]
            
            # Audit each commit
            total_issues = 0
            quality_scores = []
            
            for i, commit in enumerate(commits, 1):
                logger.info(f"   Auditing commit {i}/{len(commits)}: {commit.sha[:8]}")
                audit = self.audit_engine.audit_commit(repo_identifier, commit)
                
                # Store in RAG
                self.rag_manager.store_commit_audit(audit)
                
                total_issues += audit.total_issues
                quality_scores.append(audit.quality_score)
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            result = {
                "status": "success",
                "repo": repo_identifier,
                "commits_analyzed": len(commits),
                "strategy": strategy,
                "total_issues": total_issues,
                "avg_quality_score": round(avg_quality, 1),
                "message": f"✓ Bootstrapped {repo_identifier} ({len(commits)} commits, avg quality: {avg_quality:.1f}/100)"
            }
            
            logger.info(result["message"])
            return result
            
        except Exception as e:
            logger.error(f"Bootstrap failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": f"❌ Bootstrap failed: {e}"
            }
    
    def sync_repository(self, repo_identifier: str) -> Dict[str, Any]:
        """Check for new commits and audit them.
        
        This tool fetches commits since last audit and analyzes new ones.
        
        Args:
            repo_identifier: Repository in format 'owner/repo'
        
        Returns:
            dict with status, new_commits, quality_change
        """
        try:
            logger.info(f"🔄 Sync: {repo_identifier}")
            
            # Get last audited commit from RAG
            last_sha = self._get_last_audited_commit(repo_identifier)
            logger.info(f"   Last audited SHA from RAG: {last_sha}")
            
            # Get all commits
            commits = self.connector.list_commits(repo_identifier)
            logger.info(f"   Total commits from GitHub: {len(commits)}")
            
            # Filter to new commits
            new_commits = []
            for commit in commits:
                # Compare with startswith to handle both full and short SHAs
                if last_sha and (commit.sha == last_sha or commit.sha.startswith(last_sha)):
                    break
                new_commits.append(commit)
            
            if not new_commits:
                return {
                    "status": "success",
                    "repo": repo_identifier,
                    "new_commits": 0,
                    "message": f"✓ {repo_identifier} is up to date (no new commits)"
                }
            
            # Audit new commits
            total_issues = 0
            quality_scores = []
            
            for i, commit in enumerate(new_commits, 1):
                logger.info(f"   Auditing new commit {i}/{len(new_commits)}: {commit.sha[:8]}")
                audit = self.audit_engine.audit_commit(repo_identifier, commit)
                
                # Store in RAG
                self.rag_manager.store_commit_audit(audit)
                
                total_issues += audit.total_issues
                quality_scores.append(audit.quality_score)
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            result = {
                "status": "success",
                "repo": repo_identifier,
                "new_commits": len(new_commits),
                "total_issues": total_issues,
                "avg_quality_score": round(avg_quality, 1),
                "message": f"✓ Synced {repo_identifier} ({len(new_commits)} new commits, avg quality: {avg_quality:.1f}/100)"
            }
            
            logger.info(result["message"])
            return result
            
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": f"❌ Sync failed: {e}"
            }
    
    def query_quality_trends(
        self,
        repo_identifier: str,
        time_range_days: int = 90,
        focus_area: str = "overall"
    ) -> Dict[str, Any]:
        """Query quality trends using Gemini with RAG context.
        
        Retrieves audit context from RAG, then uses Gemini to analyze and provide insights.
        This is the proper Agent+RAG+Tools pattern: RAG provides knowledge, Gemini analyzes.
        
        Args:
            repo_identifier: Repository in format 'owner/repo'
            time_range_days: Time range to analyze (default: 90 days)
            focus_area: Focus area - 'overall', 'security', 'complexity', 'files'
        
        Returns:
            dict with analysis from Gemini
        """
        try:
            logger.info(f"📊 Query: {repo_identifier} (last {time_range_days} days, focus: {focus_area})")
            
            # Step 1: Retrieve context from RAG
            query_text = f"Show audit data for {repo_identifier} commits"
            raw_results = self.rag_manager.query_audits(
                query_text=query_text,
                top_k=10  # Get recent audits
            )
            
            if not raw_results:
                return {
                    "status": "success",
                    "message": f"No audit history found for {repo_identifier}"
                }
            
            # Step 2: Extract context text from RAG results
            context_texts = []
            for result in raw_results[:10]:  # Limit to avoid token overflow
                text = result.get("text", "")
                if text:
                    context_texts.append(text)
            
            context = "\n\n".join(context_texts)
            logger.info(f"Retrieved {len(context_texts)} audit contexts ({len(context)} chars)")
            
            # Step 3: Build prompt with context for Gemini
            prompt = f"""You are analyzing code quality trends for repository {repo_identifier}.

Here is the commit audit history from RAG storage:

{context}

Based on this data, please analyze:
1. Quality score trend (improving/stable/degrading)
2. Number of commits with data
3. Average quality score
4. Key findings about code quality

Provide a brief summary (2-3 sentences) with specific numbers."""

            # Step 4: Use Gemini via Vertex AI to analyze (Agent pattern!)
            # Use Vertex AI endpoint with project billing
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            model = GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            
            # Extract analysis
            analysis = response.text if hasattr(response, 'text') else str(response)
            
            result = {
                "status": "success",
                "repo": repo_identifier,
                "commits_found": len(context_texts),
                "analysis": analysis,
                "message": f"📊 {analysis}"
            }
            
            logger.info(f"Gemini analysis complete: {len(analysis)} chars")
            return result
            
        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": f"❌ Query failed: {e}"
            }
    
    # ==================== AGENT INTERFACE ====================
    
    def process_command(self, user_input: str) -> str:
        """Process natural language command through Gemini Agent.
        
        Args:
            user_input: Natural language command (e.g., "Bootstrap facebook/react using tags")
        
        Returns:
            Natural language response with results
        """
        logger.info(f"📝 Command: {user_input}")
        
        # For now, simple implementation without full ADK Agent
        # TODO: Implement proper ADK Agent with tool declarations
        
        # Parse command type
        lower_input = user_input.lower()
        
        if "bootstrap" in lower_input:
            # Extract repo
            words = user_input.split()
            repo = None
            for word in words:
                if "/" in word:
                    repo = word
                    break
            
            if not repo:
                return "❌ Please specify a repository (e.g., 'facebook/react')"
            
            result = self.bootstrap_repository(repo, strategy="recent", count=5)
            return result["message"]
        
        elif "sync" in lower_input:
            # Extract repo
            words = user_input.split()
            repo = None
            for word in words:
                if "/" in word:
                    repo = word
                    break
            
            if not repo:
                return "❌ Please specify a repository (e.g., 'myorg/myrepo')"
            
            result = self.sync_repository(repo)
            return result["message"]
        
        elif "query" in lower_input or "trend" in lower_input or "quality" in lower_input:
            # Extract repo
            words = user_input.split()
            repo = None
            for word in words:
                if "/" in word:
                    repo = word
                    break
            
            if not repo:
                return "❌ Please specify a repository"
            
            result = self.query_quality_trends(repo)
            return result["message"]
        
        else:
            return (
                "I understand three commands:\n"
                "1. bootstrap <repo> - Scan historical commits\n"
                "2. sync <repo> - Check for new commits\n"
                "3. query <repo> - Show quality trends\n\n"
                f"Try: 'Bootstrap facebook/react'"
            )
    
    # ==================== HELPERS ====================
    
    def _get_last_audited_commit(self, repo: str) -> Optional[str]:
        """Get SHA of last audited commit from RAG.
        
        Args:
            repo: Repository identifier
        
        Returns:
            Commit SHA or None
        """
        try:
            result = self.rag_manager.get_latest_audit(repo, audit_type="commit")
            if result and "commit_sha" in result:
                return result["commit_sha"]
            return None
        except Exception as e:
            logger.warning(f"Could not get last audit: {e}")
            return None
