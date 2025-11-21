"""Quality Guardian Agent - ADK Agent orchestrating repository quality analysis.

Uses Google ADK Agent with Gemini to parse natural language commands and coordinate
backend tools: GitHubConnector, AuditEngine, RAG Corpus.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from audit_models import CommitAudit
from audit.engine import AuditEngine
from connectors.github import GitHubConnector
from handlers.bootstrap import BootstrapHandler
from storage.rag_corpus import RAGCorpusManager

logger = logging.getLogger(__name__)


class QualityGuardianAgent:
    """ADK Agent orchestrating repository quality analysis.
    
    Natural language interface for three commands:
    - bootstrap: "Scan facebook/react using tags from 2024"
    - sync: "Check myorg/myrepo for new commits"  
    - query: "Show security trends for myorg/myrepo"
    
    Architecture:
        User Command (NL) → Gemini Agent → Tool Functions → RAG Storage
    
    Example:
        >>> agent = QualityGuardianAgent()
        >>> response = agent.process_command(
        ...     "Bootstrap myorg/myrepo using recent strategy, last 6 months"
        ... )
        >>> print(response)
        "✓ Bootstrapped myorg/myrepo (52 commits audited)"
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        google_project: Optional[str] = None,
        vertex_location: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-exp",
    ):
        """Initialize Quality Guardian Agent with ADK.
        
        Args:
            github_token: GitHub API token (or from GITHUB_TOKEN env var)
            google_project: GCP project ID (or from GOOGLE_CLOUD_PROJECT)
            vertex_location: Vertex AI location (or from VERTEX_LOCATION)
            model_name: Gemini model for command parsing
        """
        # Get credentials from environment if not provided
        self.github_token = github_token or os.getenv("GITHUB_TOKEN", "")
        self.google_project = google_project or os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.vertex_location = vertex_location or os.getenv("VERTEX_LOCATION", "us-west1")
        
        if not self.github_token:
            raise ValueError("GitHub token required (GITHUB_TOKEN env var or github_token parameter)")
        
        # Initialize backend components
        self.connector = GitHubConnector(token=self.github_token)
        self.audit_engine = AuditEngine()
        self.bootstrap_handler = BootstrapHandler(self.connector, self.audit_engine)
        self.rag_manager = RAGCorpusManager(
            project_id=self.google_project,
            location=self.vertex_location
        )
        
        # Initialize Gemini client for command parsing
        self.client = genai.Client()
        self.model_name = model_name
        
        logger.info(f"✅ Quality Guardian Agent initialized")
        logger.info(f"   Model: {model_name}")
        logger.info(f"   GitHub: Connected")
        logger.info(f"   RAG: {google_project} ({vertex_location})")

    def execute_bootstrap(
        self,
        repo: str,
        strategy: str = "tags",
        branch: Optional[str] = None,
        date_range_start: Optional[str] = None,
        date_range_end: Optional[str] = None,
    ) -> CommandResult:
        """Execute bootstrap command - historical repository scan.
        
        Args:
            repo: Repository identifier (e.g., "owner/repo")
            strategy: Sampling strategy (full, tags, weekly, monthly)
            branch: Optional branch (defaults to default branch)
            date_range_start: Optional start date (ISO format)
            date_range_end: Optional end date (ISO format)
            
        Returns:
            CommandResult with audit data and status
        """
        import time
        from datetime import datetime

        start_time = time.time()
        
        logger.info(f"🚀 Bootstrap: {repo} (strategy: {strategy})")
        
        try:
            # Parse dates if provided
            date_start = None
            date_end = None
            if date_range_start:
                date_start = datetime.fromisoformat(date_range_start)
            if date_range_end:
                date_end = datetime.fromisoformat(date_range_end)
            
            # Create bootstrap command
            command = BootstrapCommand(
                repo_identifier=repo,
                strategy=strategy,
                branch=branch,
                date_range_start=date_start,
                date_range_end=date_end,
            )
            
            # Execute bootstrap
            logger.info(f"📋 Executing bootstrap with {strategy} strategy...")
            result = self.bootstrap_handler.execute(command)
            
            if result.status != "success" or result.audit is None:
                raise RuntimeError(result.error or "Bootstrap handler returned no audit")
            
            audit = result.audit
            
            # Store in RAG
            logger.info(f"💾 Storing {audit.commits_scanned} commit audits in RAG...")
            self._store_audit_in_rag(audit)
            
            processing_time = time.time() - start_time
            
            message = (
                f"✓ Bootstrapped {repo}\n"
                f"  • Strategy: {strategy}\n"
                f"  • Commits audited: {audit.commits_scanned}\n"
                f"  • Total issues: {audit.total_issues}\n"
                f"  • Quality score: {audit.avg_quality_score:.1f}/100\n"
                f"  • Processing time: {processing_time:.1f}s"
            )
            
            logger.info(message)
            
            return CommandResult(
                command_type="bootstrap",
                status="success",
                message=message,
                audit=audit,
                processing_time=processing_time,
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Bootstrap failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return CommandResult(
                command_type="bootstrap",
                status="error",
                message=error_msg,
                error=str(e),
                processing_time=processing_time,
            )

    def execute_sync(
        self,
        repo: str,
        branch: Optional[str] = None,
        since_audit_id: Optional[str] = None,
    ) -> CommandResult:
        """Execute sync command - incremental update with new commits.
        
        Args:
            repo: Repository identifier (e.g., "owner/repo")
            branch: Optional branch (defaults to default branch)
            since_audit_id: Optional audit ID to continue from
            
        Returns:
            CommandResult with audit data and status
        """
        import time

        start_time = time.time()
        
        logger.info(f"🔄 Sync: {repo}")
        
        try:
            # Create sync command
            command = SyncCommand(
                repo_identifier=repo,
                branch=branch,
                since_audit_id=since_audit_id,
            )
            
            # Get latest audit to find last commit
            last_commit_sha = self._get_last_audited_commit(repo)
            
            # List commits since last audit
            logger.info(f"📋 Finding new commits since {last_commit_sha[:7] if last_commit_sha else 'start'}...")
            commits = self.connector.list_commits(
                repo,
                branch=branch or self.connector.get_repository_info(repo).default_branch,
            )
            
            # Filter to only new commits
            if last_commit_sha:
                new_commits = []
                for commit in commits:
                    if commit.sha == last_commit_sha:
                        break
                    new_commits.append(commit)
                commits = new_commits
            
            if not commits:
                processing_time = time.time() - start_time
                message = f"✓ {repo} is up to date (no new commits)"
                
                return CommandResult(
                    command_type="sync",
                    status="success",
                    message=message,
                    processing_time=processing_time,
                )
            
            # Audit new commits
            logger.info(f"🔍 Auditing {len(commits)} new commits...")
            audit = self.audit_engine.audit_repository(
                repo,
                commits,
                scan_type="sync",
            )
            
            # Store in RAG
            logger.info(f"💾 Storing {len(commits)} commit audits in RAG...")
            self._store_audit_in_rag(audit)
            
            processing_time = time.time() - start_time
            
            message = (
                f"✓ Synced {repo}\n"
                f"  • New commits: {len(commits)}\n"
                f"  • Total issues: {audit.total_issues}\n"
                f"  • Quality score: {audit.avg_quality_score:.1f}/100\n"
                f"  • Processing time: {processing_time:.1f}s"
            )
            
            logger.info(message)
            
            return CommandResult(
                command_type="sync",
                status="success",
                message=message,
                audit=audit,
                processing_time=processing_time,
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Sync failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return CommandResult(
                command_type="sync",
                status="error",
                message=error_msg,
                error=str(e),
                processing_time=processing_time,
            )

    def _store_audit_in_rag(self, audit: RepositoryAudit) -> None:
        """Store repository audit and all commit audits in RAG.
        
        Args:
            audit: RepositoryAudit to store
        """
        # Store repository-level audit
        self.rag_manager.store_repository_audit(audit)
        
        # Store each commit audit separately
        for commit_audit in audit.commit_audits:
            self.rag_manager.store_commit_audit(commit_audit)

    def _get_last_audited_commit(self, repo: str) -> Optional[str]:
        """Get SHA of last audited commit for a repository.
        
        Args:
            repo: Repository identifier
            
        Returns:
            Commit SHA or None if no audits found
        """
        try:
            # Query RAG for latest audit
            result = self.rag_manager.get_latest_audit(repo, audit_type="commit")
            
            if result and 'text' in result:
                # Extract commit SHA from text
                # Format: "commit_sha abc123..."
                text = result['text']
                if 'commit_sha' in text:
                    lines = text.split('\n')
                    for line in lines:
                        if line.startswith('commit_sha'):
                            sha = line.split()[-1]
                            return sha
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not retrieve last audit: {e}")
            return None
