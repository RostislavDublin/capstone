"""Tests for command parser."""

from datetime import datetime, timedelta

import pytest

from src.audit_models import BootstrapCommand, QualityQuery, SyncCommand
from src.commands import CommandParser


@pytest.fixture
def parser():
    """Create CommandParser instance."""
    return CommandParser()


def test_parse_bootstrap_basic(parser):
    """Test basic bootstrap command parsing."""
    result = parser.parse("bootstrap facebook/react")

    assert isinstance(result, BootstrapCommand)
    assert result.repo_identifier == "facebook/react"
    assert result.strategy == "tags"  # Default
    assert result.branch is None


def test_parse_bootstrap_with_strategy(parser):
    """Test bootstrap with explicit strategy."""
    result = parser.parse("bootstrap tensorflow/tensorflow using weekly")

    assert isinstance(result, BootstrapCommand)
    assert result.repo_identifier == "tensorflow/tensorflow"
    assert result.strategy == "weekly"


def test_parse_bootstrap_scan_variant(parser):
    """Test 'scan' synonym for bootstrap."""
    result = parser.parse("scan microsoft/vscode with monthly")

    assert isinstance(result, BootstrapCommand)
    assert result.repo_identifier == "microsoft/vscode"
    assert result.strategy == "monthly"


def test_parse_bootstrap_analyze_history_variant(parser):
    """Test 'analyze history' variant."""
    result = parser.parse("analyze history of golang/go full")

    assert isinstance(result, BootstrapCommand)
    assert result.repo_identifier == "golang/go"
    assert result.strategy == "full"


def test_parse_bootstrap_with_github_url(parser):
    """Test parsing GitHub URLs."""
    result = parser.parse("bootstrap https://github.com/facebook/react")

    assert isinstance(result, BootstrapCommand)
    assert result.repo_identifier == "facebook/react"


def test_parse_sync_basic(parser):
    """Test basic sync command."""
    result = parser.parse("sync facebook/react")

    assert isinstance(result, SyncCommand)
    assert result.repo_identifier == "facebook/react"
    assert result.branch is None


def test_parse_sync_check_variant(parser):
    """Test 'check for commits' variant."""
    result = parser.parse("check tensorflow/tensorflow for new commits")

    assert isinstance(result, SyncCommand)
    assert result.repo_identifier == "tensorflow/tensorflow"


def test_parse_sync_update_variant(parser):
    """Test 'update' variant."""
    result = parser.parse("update microsoft/vscode")

    assert isinstance(result, SyncCommand)
    assert result.repo_identifier == "microsoft/vscode"


def test_parse_query_what(parser):
    """Test 'what' query."""
    result = parser.parse("what is the quality trend for facebook/react?")

    assert isinstance(result, QualityQuery)
    assert result.query_text == "what is the quality trend for facebook/react?"
    assert result.repo_identifier == "facebook/react"


def test_parse_query_how(parser):
    """Test 'how' query."""
    result = parser.parse("how has security changed in tensorflow/tensorflow?")

    assert isinstance(result, QualityQuery)
    assert "security changed" in result.query_text
    assert result.repo_identifier == "tensorflow/tensorflow"
    assert result.filters == {"issue_type": "security"}


def test_parse_query_with_severity_filter(parser):
    """Test query with severity filter."""
    result = parser.parse("show me critical issues in microsoft/vscode")

    assert isinstance(result, QualityQuery)
    assert result.repo_identifier == "microsoft/vscode"
    assert result.filters == {"severity": "critical"}


def test_parse_query_with_multiple_filters(parser):
    """Test query with multiple filters."""
    result = parser.parse("show critical security issues in facebook/react")

    assert isinstance(result, QualityQuery)
    assert result.repo_identifier == "facebook/react"
    assert "security" in result.filters["issue_type"]
    assert "critical" in result.filters["severity"]


def test_extract_date_range_last_week(parser):
    """Test 'last week' date extraction."""
    start, end = parser._extract_date_range("show issues from last week")

    assert start is not None
    assert end is not None
    assert (end - start).days >= 6  # Approximately a week


def test_extract_date_range_last_month(parser):
    """Test 'last month' date extraction."""
    start, end = parser._extract_date_range("quality trend last month")

    assert start is not None
    assert end is not None
    assert (end - start).days >= 29  # Approximately a month


def test_extract_date_range_quarter(parser):
    """Test quarter date extraction."""
    start, _ = parser._extract_date_range("what changed since Q3 2024?")

    assert start is not None
    assert start.year == 2024
    assert start.month == 7  # Q3 starts in July


def test_extract_date_range_specific_dates(parser):
    """Test specific date range extraction."""
    start, end = parser._extract_date_range(
        "issues between 2024-01-01 and 2024-12-31"
    )

    assert start == datetime(2024, 1, 1)
    assert end == datetime(2024, 12, 31)


def test_extract_branch(parser):
    """Test branch name extraction."""
    branch = parser._extract_branch("bootstrap facebook/react branch main")

    assert branch == "main"


def test_extract_branch_on_variant(parser):
    """Test 'on branch' variant."""
    branch = parser._extract_branch("sync tensorflow/tensorflow on develop branch")

    assert branch == "develop"


def test_extract_repo_identifier_clean(parser):
    """Test repo identifier cleaning."""
    repo = parser._extract_repo_identifier("facebook/react.")

    assert repo == "facebook/react"


def test_extract_repo_identifier_from_url(parser):
    """Test repo extraction from GitHub URL."""
    repo = parser._extract_repo_identifier(
        "bootstrap https://github.com/facebook/react"
    )

    assert repo == "facebook/react"


def test_parse_unrecognized_command(parser):
    """Test parsing unrecognized command."""
    result = parser.parse("hello world")

    assert result is None
