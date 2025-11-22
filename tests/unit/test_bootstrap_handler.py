"""Tests for bootstrap handler."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.audit_models import BootstrapCommand, RepositoryAudit
from src.connectors.base import CommitInfo
from src.handlers.bootstrap import BootstrapHandler


@pytest.fixture
def mock_connector():
    """Create mock repository connector."""
    return Mock()


@pytest.fixture
def mock_audit_engine():
    """Create mock audit engine."""
    return Mock()


@pytest.fixture
def bootstrap_handler(mock_connector, mock_audit_engine):
    """Create bootstrap handler with mocks."""
    return BootstrapHandler(mock_connector, mock_audit_engine)


@pytest.fixture
def sample_commits():
    """Create sample commits spanning multiple weeks."""
    base_date = datetime(2024, 11, 1)
    commits = []

    # Create 30 commits over 30 days (one per day)
    for i in range(30):
        commits.append(
            CommitInfo(
                sha=f"sha{i:02d}",
                message=f"Commit {i}",
                author="Test Author",
                author_email="test@example.com",
                date=base_date - timedelta(days=i),
                files_changed=[f"file{i}.py"],
                additions=10,
                deletions=5,
            )
        )

    return commits


@pytest.fixture
def bootstrap_command():
    """Create sample bootstrap command."""
    return BootstrapCommand(
        repo_identifier="test-owner/test-repo",
        strategy="full",
        date_range_start=None,
        date_range_end=None,
        branch=None,
    )


def test_bootstrap_handler_initialization(mock_connector):
    """Test handler initialization."""
    handler = BootstrapHandler(mock_connector)
    assert handler.connector == mock_connector
    assert handler.audit_engine is not None


def test_bootstrap_handler_initialization_with_engine(mock_connector, mock_audit_engine):
    """Test handler initialization with provided engine."""
    handler = BootstrapHandler(mock_connector, mock_audit_engine)
    assert handler.connector == mock_connector
    assert handler.audit_engine == mock_audit_engine


def test_execute_full_strategy(
    bootstrap_handler, mock_connector, mock_audit_engine, sample_commits, bootstrap_command
):
    """Test executing bootstrap with full strategy."""
    # Setup mocks
    mock_connector.list_commits.return_value = sample_commits
    mock_repo_audit = Mock(spec=RepositoryAudit)
    mock_audit_engine.audit_repository.return_value = mock_repo_audit

    # Execute
    result = bootstrap_handler.execute(bootstrap_command)

    # Verify
    assert result.status == "success"
    assert result.command_type == "bootstrap"
    assert "30 commits analyzed" in result.message
    assert result.audit == mock_repo_audit

    mock_connector.list_commits.assert_called_once_with(
        "test-owner/test-repo", branch=None, since=None, until=None
    )
    mock_audit_engine.audit_repository.assert_called_once_with(
        "test-owner/test-repo", sample_commits
    )


def test_execute_weekly_strategy(
    bootstrap_handler, mock_connector, mock_audit_engine, sample_commits
):
    """Test executing bootstrap with weekly sampling."""
    command = BootstrapCommand(
        repo_identifier="test-owner/test-repo", strategy="weekly"
    )

    mock_connector.list_commits.return_value = sample_commits
    mock_repo_audit = Mock(spec=RepositoryAudit)
    mock_audit_engine.audit_repository.return_value = mock_repo_audit

    result = bootstrap_handler.execute(command)

    assert result.status == "success"
    # Should sample approximately every 7 days from 30 commits
    # Called with sampled commits (not all 30)
    call_args = mock_audit_engine.audit_repository.call_args
    sampled_commits = call_args[0][1]
    assert len(sampled_commits) < len(sample_commits)
    assert len(sampled_commits) >= 4  # At least 4 weekly samples from 30 days


def test_execute_monthly_strategy(
    bootstrap_handler, mock_connector, mock_audit_engine, sample_commits
):
    """Test executing bootstrap with monthly sampling."""
    command = BootstrapCommand(
        repo_identifier="test-owner/test-repo", strategy="monthly"
    )

    mock_connector.list_commits.return_value = sample_commits
    mock_repo_audit = Mock(spec=RepositoryAudit)
    mock_audit_engine.audit_repository.return_value = mock_repo_audit

    result = bootstrap_handler.execute(command)

    assert result.status == "success"
    # Should sample approximately every 30 days
    call_args = mock_audit_engine.audit_repository.call_args
    sampled_commits = call_args[0][1]
    assert len(sampled_commits) < len(sample_commits)
    # From 30 days of commits with 30-day interval, expect 1-2 samples
    assert len(sampled_commits) <= 2


def test_execute_with_date_range(
    bootstrap_handler, mock_connector, mock_audit_engine, sample_commits
):
    """Test executing bootstrap with date range filter."""
    start_date = datetime(2024, 10, 15)
    end_date = datetime(2024, 10, 25)

    command = BootstrapCommand(
        repo_identifier="test-owner/test-repo",
        strategy="full",
        date_range_start=start_date,
        date_range_end=end_date,
    )

    mock_connector.list_commits.return_value = sample_commits[:10]  # Subset
    mock_repo_audit = Mock(spec=RepositoryAudit)
    mock_audit_engine.audit_repository.return_value = mock_repo_audit

    result = bootstrap_handler.execute(command)

    assert result.status == "success"
    mock_connector.list_commits.assert_called_once_with(
        "test-owner/test-repo", branch=None, since=start_date, until=end_date
    )


def test_execute_with_branch(
    bootstrap_handler, mock_connector, mock_audit_engine, sample_commits
):
    """Test executing bootstrap on specific branch."""
    command = BootstrapCommand(
        repo_identifier="test-owner/test-repo", strategy="full", branch="develop"
    )

    mock_connector.list_commits.return_value = sample_commits
    mock_repo_audit = Mock(spec=RepositoryAudit)
    mock_audit_engine.audit_repository.return_value = mock_repo_audit

    result = bootstrap_handler.execute(command)

    assert result.status == "success"
    mock_connector.list_commits.assert_called_once_with(
        "test-owner/test-repo", branch="develop", since=None, until=None
    )


def test_execute_no_commits_found(
    bootstrap_handler, mock_connector, mock_audit_engine
):
    """Test handling when no commits are found."""
    command = BootstrapCommand(
        repo_identifier="test-owner/test-repo", strategy="full"
    )

    mock_connector.list_commits.return_value = []

    result = bootstrap_handler.execute(command)

    assert result.status == "error"
    assert "No commits found" in result.message
    mock_audit_engine.audit_repository.assert_not_called()


def test_execute_connector_error(
    bootstrap_handler, mock_connector, mock_audit_engine
):
    """Test handling connector errors."""
    command = BootstrapCommand(
        repo_identifier="test-owner/test-repo", strategy="full"
    )

    mock_connector.list_commits.side_effect = Exception("Connection failed")

    result = bootstrap_handler.execute(command)

    assert result.status == "error"
    assert "Bootstrap failed" in result.message
    assert "Connection failed" in result.message


def test_execute_audit_engine_error(
    bootstrap_handler, mock_connector, mock_audit_engine, sample_commits
):
    """Test handling audit engine errors."""
    command = BootstrapCommand(
        repo_identifier="test-owner/test-repo", strategy="full"
    )

    mock_connector.list_commits.return_value = sample_commits
    mock_audit_engine.audit_repository.side_effect = Exception("Audit failed")

    result = bootstrap_handler.execute(command)

    assert result.status == "error"
    assert "Bootstrap failed" in result.message
    assert "Audit failed" in result.message


def test_sample_by_interval_weekly(bootstrap_handler, sample_commits):
    """Test weekly interval sampling."""
    sampled = bootstrap_handler._sample_by_interval(sample_commits, days=7)

    # Should include first commit plus approximately every 7th day
    assert len(sampled) >= 4  # 30 days / 7 days ≈ 4-5 commits
    assert len(sampled) <= 5
    assert sampled[0] == sample_commits[0]  # Always includes latest


def test_sample_by_interval_monthly(bootstrap_handler, sample_commits):
    """Test monthly interval sampling."""
    sampled = bootstrap_handler._sample_by_interval(sample_commits, days=30)

    # Should include first commit plus one more from 30 days ago
    assert len(sampled) <= 2
    assert sampled[0] == sample_commits[0]


def test_sample_by_interval_empty_commits(bootstrap_handler):
    """Test interval sampling with empty commit list."""
    sampled = bootstrap_handler._sample_by_interval([], days=7)
    assert len(sampled) == 0


def test_sample_by_interval_single_commit(bootstrap_handler):
    """Test interval sampling with single commit."""
    commit = CommitInfo(
        sha="abc123",
        message="Single commit",
        author="Test",
        author_email="test@example.com",
        date=datetime(2024, 11, 1),
        files_changed=["file.py"],
        additions=10,
        deletions=5,
    )

    sampled = bootstrap_handler._sample_by_interval([commit], days=7)
    assert len(sampled) == 1
    assert sampled[0] == commit


def test_apply_sampling_full(bootstrap_handler, sample_commits):
    """Test full sampling strategy."""
    sampled = bootstrap_handler._apply_sampling("full", sample_commits)
    assert sampled == sample_commits


def test_apply_sampling_weekly(bootstrap_handler, sample_commits):
    """Test weekly sampling strategy."""
    sampled = bootstrap_handler._apply_sampling("weekly", sample_commits)
    assert len(sampled) < len(sample_commits)
    assert len(sampled) >= 4


def test_apply_sampling_monthly(bootstrap_handler, sample_commits):
    """Test monthly sampling strategy."""
    sampled = bootstrap_handler._apply_sampling("monthly", sample_commits)
    assert len(sampled) < len(sample_commits)
    assert len(sampled) <= 2


def test_apply_sampling_tags(bootstrap_handler, sample_commits):
    """Test tags sampling strategy (placeholder)."""
    # Currently returns full list with warning
    sampled = bootstrap_handler._apply_sampling("tags", sample_commits)
    assert sampled == sample_commits


def test_apply_sampling_unknown_strategy(bootstrap_handler, sample_commits):
    """Test unknown strategy falls back to full."""
    sampled = bootstrap_handler._apply_sampling("unknown", sample_commits)
    assert sampled == sample_commits


def test_execution_time_tracking(
    bootstrap_handler, mock_connector, mock_audit_engine, sample_commits
):
    """Test that execution time is properly tracked."""
    command = BootstrapCommand(
        repo_identifier="test-owner/test-repo", strategy="full"
    )

    mock_connector.list_commits.return_value = sample_commits
    mock_repo_audit = Mock(spec=RepositoryAudit)
    mock_audit_engine.audit_repository.return_value = mock_repo_audit

    result = bootstrap_handler.execute(command)

    assert result.status == "success"
    assert result.processing_time > 0
    assert isinstance(result.processing_time, float)
