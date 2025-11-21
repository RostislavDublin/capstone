"""Quality Guardian Agent - Main orchestrator for repository quality analysis.

Coordinates all components to execute bootstrap, sync, and query commands.
"""

import logging
from typing import Optional

from audit_models import BootstrapCommand, CommandResult, RepositoryAudit, SyncCommand
from audit.engine import AuditEngine
from connectors.base import RepositoryConnector
from handlers.bootstrap import BootstrapHandler
from storage.rag_corpus import RAGCorpusManager

logger = logging.getLogger(__name__)


class QualityGuardianAgent:
    """Main agent orchestrating repository quality analysis.
    
    Executes commands:
    - bootstrap: Historical scan of repository
    - sync: Incremental update with new commits
    - query: Natural language queries about quality (coming soon)
    
    Architecture:
        Command → Bootstrap/Sync Handler → Audit Engine → RAG Storage
    
    Example:
        >>> agent = QualityGuardianAgent(connector, rag_manager)
        >>> result = agent.execute_bootstrap(
        ...     repo="owner/repo",
        ...     strategy="tags"
        ... )
        >>> print(result.message)
        "✓ Bootstrapped owner/repo (15 commits audited)"
    """

    def __init__(
        self,
        connector: RepositoryConnector,
        rag_manager: RAGCorpusManager,
        audit_engine: Optional[AuditEngine] = None,
        bootstrap_handler: Optional[BootstrapHandler] = None,
    ):
        """Initialize Quality Guardian Agent.
        
        Args:
            connector: Repository connector (GitHub, GitLab, etc.)
            rag_manager: RAG corpus manager for storage
            audit_engine: Optional pre-configured audit engine
            bootstrap_handler: Optional pre-configured bootstrap handler
        """
        self.connector = connector
        self.rag_manager = rag_manager
        
        # Create audit engine if not provided
        self.audit_engine = audit_engine or AuditEngine(connector)
        
        # Create bootstrap handler if not provided
        self.bootstrap_handler = bootstrap_handler or BootstrapHandler(
            connector, self.audit_engine
        )

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
