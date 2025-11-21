"""Command parser for conversational interface."""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Union

from src.audit_models import BootstrapCommand, QualityQuery, SyncCommand


class CommandParser:
    """Parses natural language commands into structured commands."""

    # Command patterns
    BOOTSTRAP_PATTERNS = [
        r"bootstrap\s+(.+?)(?:\s+using\s+(full|tags|weekly|monthly))?$",
        r"scan\s+(.+?)(?:\s+with\s+(full|tags|weekly|monthly))?$",
        r"analyze\s+history\s+of\s+(.+?)(?:\s+(full|tags|weekly|monthly))?$",
    ]

    SYNC_PATTERNS = [
        r"sync\s+(.+)",
        r"check\s+(.+?)\s+for\s+(?:new\s+)?commits",
        r"update\s+(.+)",
    ]

    QUERY_PATTERNS = [
        r"(?:what|how|when|why|where|which|show|tell)\s+(.+)",
        r"(?:has|have|did)\s+(.+)",
    ]

    def parse(
        self, command_text: str
    ) -> Union[BootstrapCommand, SyncCommand, QualityQuery, None]:
        """Parse natural language command.

        Args:
            command_text: User's command text

        Returns:
            Structured command object or None if unrecognized
        """
        command_text = command_text.strip().lower()

        # Try bootstrap patterns
        for pattern in self.BOOTSTRAP_PATTERNS:
            match = re.search(pattern, command_text, re.IGNORECASE)
            if match:
                return self._parse_bootstrap(match, command_text)

        # Try sync patterns
        for pattern in self.SYNC_PATTERNS:
            match = re.search(pattern, command_text, re.IGNORECASE)
            if match:
                return self._parse_sync(match, command_text)

        # Try query patterns
        for pattern in self.QUERY_PATTERNS:
            match = re.search(pattern, command_text, re.IGNORECASE)
            if match:
                return self._parse_query(command_text)

        return None

    def _parse_bootstrap(
        self, match: re.Match, command_text: str
    ) -> BootstrapCommand:
        """Parse bootstrap command details.

        Args:
            match: Regex match object
            command_text: Full command text

        Returns:
            BootstrapCommand object
        """
        repo = match.group(1).strip()
        strategy = match.group(2) if match.lastindex >= 2 else "tags"

        # Clean repo identifier
        repo = self._extract_repo_identifier(repo)

        # Extract date range if present
        date_start, date_end = self._extract_date_range(command_text)

        # Extract branch if present
        branch = self._extract_branch(command_text)

        return BootstrapCommand(
            repo_identifier=repo,
            strategy=strategy,
            date_range_start=date_start,
            date_range_end=date_end,
            branch=branch,
        )

    def _parse_sync(self, match: re.Match, command_text: str) -> SyncCommand:
        """Parse sync command details.

        Args:
            match: Regex match object
            command_text: Full command text

        Returns:
            SyncCommand object
        """
        repo = match.group(1).strip()
        repo = self._extract_repo_identifier(repo)

        # Extract branch if present
        branch = self._extract_branch(command_text)

        return SyncCommand(repo_identifier=repo, branch=branch)

    def _parse_query(self, command_text: str) -> QualityQuery:
        """Parse quality query.

        Args:
            command_text: Full command text

        Returns:
            QualityQuery object
        """
        # Extract repository if mentioned
        repo = self._extract_repo_identifier(command_text)

        # Extract filters if present
        filters = {}
        if "security" in command_text:
            filters["issue_type"] = "security"
        if "complexity" in command_text:
            filters["issue_type"] = "complexity"
        if "critical" in command_text:
            filters["severity"] = "critical"
        if "high" in command_text:
            filters["severity"] = "high"

        # Extract date range
        date_start, date_end = self._extract_date_range(command_text)
        if date_start or date_end:
            filters["date_range"] = f"{date_start or ''} to {date_end or ''}"

        return QualityQuery(
            query_text=command_text,
            repo_identifier=repo,
            filters=filters if filters else None,
        )

    def _extract_repo_identifier(self, text: str) -> str:
        """Extract GitHub repository identifier.

        Args:
            text: Text potentially containing repo identifier

        Returns:
            Repository identifier in format "owner/repo"
        """
        # Pattern: owner/repo (with optional https://github.com/)
        patterns = [
            r"github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)",
            r"\b([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                repo = match.group(1)
                # Clean trailing punctuation
                repo = re.sub(r"[.,;:!?]+$", "", repo)
                return repo

        # If no pattern matches, use the text as-is (could be just repo name)
        return text.strip()

    def _extract_branch(self, text: str) -> Optional[str]:
        """Extract branch name from command text.

        Args:
            text: Command text

        Returns:
            Branch name or None
        """
        patterns = [
            r"branch\s+([a-zA-Z0-9_/-]+)",
            r"on\s+([a-zA-Z0-9_/-]+)\s+branch",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_date_range(
        self, text: str
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Extract date range from command text.

        Args:
            text: Command text

        Returns:
            Tuple of (start_date, end_date) or (None, None)
        """
        # Relative dates
        if "last week" in text:
            return datetime.now() - timedelta(weeks=1), datetime.now()
        if "last month" in text:
            return datetime.now() - timedelta(days=30), datetime.now()
        if "last year" in text:
            return datetime.now() - timedelta(days=365), datetime.now()
        if "last 3 months" in text or "last quarter" in text:
            return datetime.now() - timedelta(days=90), datetime.now()

        # Quarter patterns
        quarter_match = re.search(r"(?:since|from)\s+(Q[1-4])\s*(\d{4})", text)
        if quarter_match:
            quarter = quarter_match.group(1)
            year = int(quarter_match.group(2))
            quarter_num = int(quarter[1])
            start_month = (quarter_num - 1) * 3 + 1
            start_date = datetime(year, start_month, 1)
            return start_date, datetime.now()

        # Specific date patterns (YYYY-MM-DD)
        date_pattern = r"\d{4}-\d{2}-\d{2}"
        dates = re.findall(date_pattern, text)
        if len(dates) >= 2:
            return datetime.fromisoformat(dates[0]), datetime.fromisoformat(dates[1])
        if len(dates) == 1:
            return datetime.fromisoformat(dates[0]), None

        return None, None
