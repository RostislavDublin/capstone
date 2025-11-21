"""Bootstrap handler for initial repository scanning."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from src.audit.engine import AuditEngine
from src.audit_models import BootstrapCommand, CommandResult, RepositoryAudit
from src.connectors.base import CommitInfo, RepositoryConnector

logger = logging.getLogger(__name__)


class BootstrapHandler:
    """Handles bootstrap commands for initial repository scanning."""

    def __init__(
        self, connector: RepositoryConnector, audit_engine: Optional[AuditEngine] = None
    ):
        """Initialize handler.

        Args:
            connector: Repository connector for accessing commits
            audit_engine: Optional audit engine (creates one if not provided)
        """
        self.connector = connector
        self.audit_engine = audit_engine or AuditEngine(connector)

    def execute(self, command: BootstrapCommand) -> CommandResult:
        """Execute bootstrap command.

        Args:
            command: Bootstrap command to execute

        Returns:
            CommandResult with execution status and results
        """
        start_time = datetime.now()
        logger.info(
            f"Starting bootstrap for {command.repo_identifier} "
            f"with strategy: {command.strategy}"
        )

        try:
            # Get all commits from repository
            all_commits = self._fetch_commits(command)
            logger.info(f"Found {len(all_commits)} total commits")

            # Apply sampling strategy
            sampled_commits = self._apply_sampling(command.strategy, all_commits)
            logger.info(
                f"After {command.strategy} sampling: {len(sampled_commits)} commits"
            )

            if not sampled_commits:
                return CommandResult(
                    command_type="bootstrap",
                    status="error",
                    message="No commits found after sampling",
                    processing_time=(datetime.now() - start_time).total_seconds(),
                )

            # Audit the sampled commits
            repo_audit = self.audit_engine.audit_repository(
                command.repo_identifier, sampled_commits
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Bootstrap complete: {len(sampled_commits)} commits audited "
                f"in {processing_time:.2f}s"
            )

            return CommandResult(
                command_type="bootstrap",
                status="success",
                message=f"Successfully bootstrapped {command.repo_identifier} "
                f"({len(sampled_commits)} commits analyzed)",
                audit=repo_audit,
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Bootstrap failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return CommandResult(
                command_type="bootstrap",
                status="error",
                message=error_msg,
                error=str(e),
                processing_time=processing_time,
            )

    def _fetch_commits(self, command: BootstrapCommand) -> List[CommitInfo]:
        """Fetch commits based on command parameters.

        Args:
            command: Bootstrap command with repo and date range

        Returns:
            List of commits matching criteria
        """
        return self.connector.list_commits(
            command.repo_identifier,
            branch=command.branch,
            since=command.date_range_start,
            until=command.date_range_end,
        )

    def _apply_sampling(
        self, strategy: str, commits: List[CommitInfo]
    ) -> List[CommitInfo]:
        """Apply sampling strategy to reduce number of commits.

        Args:
            strategy: Sampling strategy (full, tags, weekly, monthly)
            commits: All commits from repository

        Returns:
            Filtered list of commits based on strategy
        """
        if strategy == "full":
            return commits

        elif strategy == "tags":
            return self._sample_by_tags(commits)

        elif strategy == "weekly":
            return self._sample_by_interval(commits, days=7)

        elif strategy == "monthly":
            return self._sample_by_interval(commits, days=30)

        else:
            logger.warning(f"Unknown strategy '{strategy}', using full")
            return commits

    def _sample_by_tags(self, commits: List[CommitInfo]) -> List[CommitInfo]:
        """Sample commits at tag points.

        Args:
            commits: All commits

        Returns:
            Commits that have tags (release points)
        """
        # Get all tags from repository
        # For now, return commits - will implement tag matching when we have repo_identifier
        # This is a placeholder that should be enhanced with actual tag matching
        logger.warning("Tag-based sampling not fully implemented yet, using full list")
        return commits

    def _sample_by_interval(
        self, commits: List[CommitInfo], days: int
    ) -> List[CommitInfo]:
        """Sample commits at regular time intervals.

        Args:
            commits: All commits (assumed sorted newest to oldest)
            days: Number of days between samples

        Returns:
            Sampled commits at specified intervals
        """
        if not commits:
            return []

        sampled = [commits[0]]  # Always include latest commit
        last_date = commits[0].date
        interval = timedelta(days=days)

        for commit in commits[1:]:
            # Check if enough time has passed since last sampled commit
            if last_date - commit.date >= interval:
                sampled.append(commit)
                last_date = commit.date

        logger.info(
            f"Sampled {len(sampled)} commits using {days}-day interval "
            f"(from {len(commits)} total)"
        )
        return sampled
