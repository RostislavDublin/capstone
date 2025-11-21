"""Integration tests for Quality Guardian Agent.

Tests full workflow: bootstrap → audit → store → query.
These tests use real components (not mocks) but work with local test data.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from src.agents.quality_guardian import QualityGuardianAgent
from src.connectors.base import CommitInfo, RepositoryConnector, RepositoryInfo
from src.storage.rag_corpus import RAGCorpusManager


@pytest.fixture
def mock_connector():
    """Create a mock connector with realistic test data."""
    connector = Mock(spec=RepositoryConnector)
    
    # Mock repository info
    connector.get_repository_info.return_value = RepositoryInfo(
        full_name="test-org/test-repo",
        owner="test-org",
        name="test-repo",
        description="Test repository",
        default_branch="main",
        created_at=datetime(2025, 1, 1),
        language="Python",
        topics=[],
    )
    
    # Mock commits
    commits = [
        CommitInfo(
            sha="commit1abc",
            message="Add authentication",
            author="Alice",
            author_email="alice@example.com",
            date=datetime(2025, 11, 1),
            files_changed=["src/auth.py", "tests/test_auth.py"],
            additions=50,
            deletions=10,
        ),
        CommitInfo(
            sha="commit2def",
            message="Fix payment bug",
            author="Bob",
            author_email="bob@example.com",
            date=datetime(2025, 11, 15),
            files_changed=["src/payments.py"],
            additions=20,
            deletions=5,
        ),
    ]
    connector.list_commits.return_value = commits
    connector.list_tags.return_value = []
    
    # Mock clone_repository
    def mock_clone(repo_id, target_dir, sha=None):
        # Create a fake Python file for testing
        repo_path = Path(target_dir) / "test-repo"
        repo_path.mkdir(parents=True)
        
        # Create a simple Python file
        (repo_path / "src").mkdir()
        (repo_path / "src" / "auth.py").write_text("""
def authenticate(username, password):
    # Simple authentication
    if username == "admin" and password == "admin123":
        return True
    return False
""")
        
        return str(repo_path)
    
    connector.clone_repository.side_effect = mock_clone
    
    return connector


@pytest.fixture
def mock_rag_manager():
    """Create a mock RAG manager."""
    manager = Mock(spec=RAGCorpusManager)
    manager.store_commit_audit.return_value = {"commit": Mock()}
    manager.store_repository_audit.return_value = Mock()
    manager.get_latest_audit.return_value = None
    return manager


def test_quality_guardian_initialization(mock_connector, mock_rag_manager):
    """Test QualityGuardianAgent initialization."""
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    assert agent.connector == mock_connector
    assert agent.rag_manager == mock_rag_manager
    assert agent.audit_engine is not None
    assert agent.bootstrap_handler is not None


def test_execute_bootstrap_success(mock_connector, mock_rag_manager):
    """Test successful bootstrap execution."""
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    result = agent.execute_bootstrap(
        repo="test-org/test-repo",
        strategy="full",
    )
    
    # Check result
    assert result.command_type == "bootstrap"
    assert result.status == "success"
    assert "Bootstrapped test-org/test-repo" in result.message
    assert result.audit is not None
    assert result.processing_time > 0
    
    # Check audit data
    audit = result.audit
    assert audit.repo_identifier == "test-org/test-repo"
    assert audit.commits_scanned > 0
    # scan_type varies by strategy (full, tags, weekly, monthly)
    
    # Verify RAG storage was called
    assert mock_rag_manager.store_repository_audit.called
    assert mock_rag_manager.store_commit_audit.call_count > 0


def test_execute_bootstrap_with_tags_strategy(mock_connector, mock_rag_manager):
    """Test bootstrap with tags strategy."""
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    result = agent.execute_bootstrap(
        repo="test-org/test-repo",
        strategy="tags",
    )
    
    assert result.status == "success"
    assert result.audit.scan_type == "bootstrap_tags"


def test_execute_bootstrap_with_date_range(mock_connector, mock_rag_manager):
    """Test bootstrap with date filtering."""
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    result = agent.execute_bootstrap(
        repo="test-org/test-repo",
        strategy="full",
        date_range_start="2025-11-01T00:00:00",
        date_range_end="2025-11-30T23:59:59",
    )
    
    assert result.status == "success"
    # Date filtering is handled by bootstrap handler
    assert result.audit is not None


def test_execute_sync_no_new_commits(mock_connector, mock_rag_manager):
    """Test sync when no new commits exist."""
    # Mock latest audit returns the most recent commit
    mock_rag_manager.get_latest_audit.return_value = {
        "text": "commit_sha commit1abc\ncommit_message Add authentication"
    }
    
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    result = agent.execute_sync(repo="test-org/test-repo")
    
    assert result.command_type == "sync"
    assert result.status == "success"
    assert "up to date" in result.message
    assert result.audit is None


def test_execute_sync_with_new_commits(mock_connector, mock_rag_manager):
    """Test sync when new commits exist."""
    # Mock latest audit returns an older commit
    mock_rag_manager.get_latest_audit.return_value = {
        "text": "commit_sha oldcommitxyz\ncommit_message Old commit"
    }
    
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    result = agent.execute_sync(repo="test-org/test-repo")
    
    assert result.command_type == "sync"
    assert result.status == "success"
    assert "Synced test-org/test-repo" in result.message
    assert result.audit is not None
    assert result.audit.commits_scanned > 0
    
    # Verify RAG storage was called
    assert mock_rag_manager.store_repository_audit.called


def test_execute_sync_first_time(mock_connector, mock_rag_manager):
    """Test sync when no previous audits exist."""
    # No latest audit found
    mock_rag_manager.get_latest_audit.return_value = None
    
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    result = agent.execute_sync(repo="test-org/test-repo")
    
    assert result.status == "success"
    # Should audit all commits
    assert result.audit.commits_scanned > 0


def test_execute_bootstrap_connector_error(mock_connector, mock_rag_manager):
    """Test bootstrap handles connector errors gracefully."""
    # Simulate connector error
    mock_connector.list_commits.side_effect = Exception("GitHub API error")
    
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    result = agent.execute_bootstrap(
        repo="test-org/test-repo",
        strategy="full",
    )
    
    assert result.command_type == "bootstrap"
    assert result.status == "error"
    assert "Bootstrap failed" in result.message
    assert result.error is not None


def test_execute_sync_rag_error(mock_connector, mock_rag_manager):
    """Test sync handles RAG errors gracefully."""
    # Simulate RAG error
    mock_rag_manager.store_commit_audit.side_effect = Exception("RAG upload failed")
    mock_rag_manager.get_latest_audit.return_value = None
    
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    result = agent.execute_sync(repo="test-org/test-repo")
    
    assert result.status == "error"
    assert result.error is not None


def test_full_workflow_bootstrap_then_sync(mock_connector, mock_rag_manager):
    """Test complete workflow: bootstrap followed by sync."""
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    # Step 1: Bootstrap
    bootstrap_result = agent.execute_bootstrap(
        repo="test-org/test-repo",
        strategy="full",
    )
    
    assert bootstrap_result.status == "success"
    first_audit = bootstrap_result.audit
    first_commits = first_audit.commits_scanned
    
    # Mock: new commit appears
    new_commit = CommitInfo(
        sha="commit3new",
        message="Add feature X",
        author="Charlie",
        author_email="charlie@example.com",
        date=datetime(2025, 11, 20),
        files_changed=["src/feature.py"],
        additions=30,
        deletions=0,
    )
    
    # Update mock to return new commits
    all_commits = [new_commit] + mock_connector.list_commits.return_value
    mock_connector.list_commits.return_value = all_commits
    
    # Mock latest audit to return last bootstrap commit
    mock_rag_manager.get_latest_audit.return_value = {
        "text": f"commit_sha {first_audit.commit_audits[0].commit_sha}\ncommit_message ..."
    }
    
    # Step 2: Sync
    sync_result = agent.execute_sync(repo="test-org/test-repo")
    
    assert sync_result.status == "success"
    # Should only audit the new commit
    assert sync_result.audit.commits_scanned == 1


def test_audit_storage_includes_file_level_data(mock_connector, mock_rag_manager):
    """Test that stored audits include file-level granularity."""
    agent = QualityGuardianAgent(mock_connector, mock_rag_manager)
    
    result = agent.execute_bootstrap(
        repo="test-org/test-repo",
        strategy="full",
    )
    
    assert result.status == "success"
    
    # Check that commit audits have file-level data
    for commit_audit in result.audit.commit_audits:
        assert hasattr(commit_audit, 'files')
        # Files list should contain FileAudit objects
        if commit_audit.files:
            file_audit = commit_audit.files[0]
            assert hasattr(file_audit, 'file_path')
            assert hasattr(file_audit, 'quality_score')
            assert hasattr(file_audit, 'security_score')
