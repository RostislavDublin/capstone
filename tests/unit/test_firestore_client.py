"""Unit tests for Firestore client."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

import sys
sys.path.insert(0, 'src')

from storage.firestore_client import FirestoreAuditDB
from audit_models import CommitAudit


@pytest.fixture
def mock_firestore_client():
    """Mock Firestore client."""
    with patch('storage.firestore_client.firestore.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_commit_audit():
    """Sample CommitAudit for testing."""
    return CommitAudit(
        repository="facebook/react",
        commit_sha="abc123def456",
        commit_message="Fix security issue",
        author="John Doe",
        author_email="john@example.com",
        date=datetime(2024, 1, 15, 10, 30),
        files_changed=["src/auth.py", "src/db.py"],
        security_score=85.5,
        quality_score=92.3,
        security_issues=[],
        complexity_issues=[],
        code_quality_issues=[],
        overall_assessment="Good commit with security improvements",
    )


def test_init_default_params(mock_firestore_client):
    """Test FirestoreAuditDB initialization with default parameters."""
    db = FirestoreAuditDB()
    
    assert db.collection_prefix == "quality-guardian"
    assert db.repositories_collection == "quality-guardian-repositories"


def test_init_custom_params(mock_firestore_client):
    """Test FirestoreAuditDB initialization with custom parameters."""
    db = FirestoreAuditDB(
        project_id="test-project",
        database="test-db",
        collection_prefix="custom-prefix"
    )
    
    assert db.collection_prefix == "custom-prefix"
    assert db.repositories_collection == "custom-prefix-repositories"


def test_get_repo_id():
    """Test repository name to document ID conversion."""
    with patch('storage.firestore_client.firestore.Client'):
        db = FirestoreAuditDB()
        
        assert db._get_repo_id("facebook/react") == "facebook_react"
        assert db._get_repo_id("google/guava") == "google_guava"


def test_store_commit_audit_new_repo(mock_firestore_client, sample_commit_audit):
    """Test storing commit audit for a new repository."""
    # Setup mocks
    mock_collection = MagicMock()
    mock_repo_doc_ref = MagicMock()
    mock_repo_doc = MagicMock()
    mock_repo_doc.exists = False
    mock_repo_doc_ref.get.return_value = mock_repo_doc
    
    mock_commit_ref = MagicMock()
    mock_commits_collection = MagicMock()
    mock_commits_collection.document.return_value = mock_commit_ref
    mock_repo_doc_ref.collection.return_value = mock_commits_collection
    
    mock_collection.document.return_value = mock_repo_doc_ref
    mock_firestore_client.collection.return_value = mock_collection
    
    # Execute
    db = FirestoreAuditDB()
    db.store_commit_audit(sample_commit_audit)
    
    # Verify repository document was created
    mock_repo_doc_ref.set.assert_called_once()
    repo_data = mock_repo_doc_ref.set.call_args[0][0]
    assert repo_data["name"] == "facebook/react"
    assert repo_data["total_commits"] == 1
    
    # Verify commit was stored
    mock_commit_ref.set.assert_called_once()
    commit_data = mock_commit_ref.set.call_args[0][0]
    assert commit_data["commit_sha"] == "abc123def456"
    assert commit_data["repository"] == "facebook/react"


def test_store_commit_audit_existing_repo(mock_firestore_client, sample_commit_audit):
    """Test storing commit audit for an existing repository."""
    # Setup mocks
    mock_collection = MagicMock()
    mock_repo_doc_ref = MagicMock()
    mock_repo_doc = MagicMock()
    mock_repo_doc.exists = True
    mock_repo_doc_ref.get.return_value = mock_repo_doc
    
    mock_commit_ref = MagicMock()
    mock_commits_collection = MagicMock()
    mock_commits_collection.document.return_value = mock_commit_ref
    mock_repo_doc_ref.collection.return_value = mock_commits_collection
    
    mock_collection.document.return_value = mock_repo_doc_ref
    mock_firestore_client.collection.return_value = mock_collection
    
    # Execute
    db = FirestoreAuditDB()
    db.store_commit_audit(sample_commit_audit)
    
    # Verify repository document was updated
    mock_repo_doc_ref.update.assert_called_once()
    
    # Verify commit was stored
    mock_commit_ref.set.assert_called_once()


def test_get_repositories_empty(mock_firestore_client):
    """Test get_repositories when no repositories exist."""
    mock_collection = MagicMock()
    mock_collection.stream.return_value = []
    mock_firestore_client.collection.return_value = mock_collection
    
    db = FirestoreAuditDB()
    repos = db.get_repositories()
    
    assert repos == []


def test_get_repositories_multiple(mock_firestore_client):
    """Test get_repositories with multiple repositories."""
    # Setup mock documents
    mock_doc1 = MagicMock()
    mock_doc1.to_dict.return_value = {"name": "facebook/react"}
    
    mock_doc2 = MagicMock()
    mock_doc2.to_dict.return_value = {"name": "google/guava"}
    
    mock_doc3 = MagicMock()
    mock_doc3.to_dict.return_value = {"name": "apache/kafka"}
    
    mock_collection = MagicMock()
    mock_collection.stream.return_value = [mock_doc1, mock_doc2, mock_doc3]
    mock_firestore_client.collection.return_value = mock_collection
    
    db = FirestoreAuditDB()
    repos = db.get_repositories()
    
    assert len(repos) == 3
    assert "facebook/react" in repos
    assert "google/guava" in repos
    assert "apache/kafka" in repos
    assert repos == sorted(repos)  # Should be sorted


def test_query_by_repository_not_found(mock_firestore_client):
    """Test query_by_repository when repository doesn't exist."""
    mock_collection = MagicMock()
    mock_repo_doc_ref = MagicMock()
    mock_repo_doc = MagicMock()
    mock_repo_doc.exists = False
    mock_repo_doc_ref.get.return_value = mock_repo_doc
    
    mock_collection.document.return_value = mock_repo_doc_ref
    mock_firestore_client.collection.return_value = mock_collection
    
    db = FirestoreAuditDB()
    audits = db.query_by_repository("nonexistent/repo")
    
    assert audits == []


def test_query_by_repository_with_results(mock_firestore_client, sample_commit_audit):
    """Test query_by_repository returns commit audits."""
    # Setup mocks
    mock_collection = MagicMock()
    mock_repo_doc_ref = MagicMock()
    mock_repo_doc = MagicMock()
    mock_repo_doc.exists = True
    mock_repo_doc_ref.get.return_value = mock_repo_doc
    
    # Mock commits query
    mock_commits_collection = MagicMock()
    mock_query = MagicMock()
    mock_query.limit.return_value = mock_query
    
    # Mock commit document
    mock_commit_doc = MagicMock()
    mock_commit_doc.to_dict.return_value = sample_commit_audit.model_dump()
    mock_query.stream.return_value = [mock_commit_doc]
    
    mock_commits_collection.order_by.return_value = mock_query
    mock_repo_doc_ref.collection.return_value = mock_commits_collection
    
    mock_collection.document.return_value = mock_repo_doc_ref
    mock_firestore_client.collection.return_value = mock_collection
    
    # Execute
    db = FirestoreAuditDB()
    audits = db.query_by_repository("facebook/react", limit=10)
    
    assert len(audits) == 1
    assert audits[0].commit_sha == "abc123def456"
    assert audits[0].repository == "facebook/react"


def test_get_repository_stats_found(mock_firestore_client):
    """Test get_repository_stats returns stats."""
    mock_collection = MagicMock()
    mock_repo_doc_ref = MagicMock()
    mock_repo_doc = MagicMock()
    mock_repo_doc.exists = True
    mock_repo_doc.to_dict.return_value = {
        "name": "facebook/react",
        "total_commits": 42,
        "first_analyzed": datetime(2024, 1, 1),
        "last_analyzed": datetime(2024, 1, 15),
    }
    mock_repo_doc_ref.get.return_value = mock_repo_doc
    
    mock_collection.document.return_value = mock_repo_doc_ref
    mock_firestore_client.collection.return_value = mock_collection
    
    db = FirestoreAuditDB()
    stats = db.get_repository_stats("facebook/react")
    
    assert stats is not None
    assert stats["name"] == "facebook/react"
    assert stats["total_commits"] == 42


def test_get_repository_stats_not_found(mock_firestore_client):
    """Test get_repository_stats returns None when not found."""
    mock_collection = MagicMock()
    mock_repo_doc_ref = MagicMock()
    mock_repo_doc = MagicMock()
    mock_repo_doc.exists = False
    mock_repo_doc_ref.get.return_value = mock_repo_doc
    
    mock_collection.document.return_value = mock_repo_doc_ref
    mock_firestore_client.collection.return_value = mock_collection
    
    db = FirestoreAuditDB()
    stats = db.get_repository_stats("nonexistent/repo")
    
    assert stats is None


def test_delete_repository_success(mock_firestore_client):
    """Test delete_repository successfully deletes data."""
    # Setup mocks
    mock_collection = MagicMock()
    mock_repo_doc_ref = MagicMock()
    mock_repo_doc = MagicMock()
    mock_repo_doc.exists = True
    mock_repo_doc_ref.get.return_value = mock_repo_doc
    
    # Mock commits subcollection
    mock_commits_collection = MagicMock()
    mock_commit_doc1 = MagicMock()
    mock_commit_doc2 = MagicMock()
    mock_commits_collection.stream.return_value = [mock_commit_doc1, mock_commit_doc2]
    mock_repo_doc_ref.collection.return_value = mock_commits_collection
    
    mock_collection.document.return_value = mock_repo_doc_ref
    mock_firestore_client.collection.return_value = mock_collection
    
    # Mock batch
    mock_batch = MagicMock()
    mock_firestore_client.batch.return_value = mock_batch
    
    # Execute
    db = FirestoreAuditDB()
    result = db.delete_repository("facebook/react")
    
    assert result is True
    mock_repo_doc_ref.delete.assert_called_once()
    assert mock_batch.delete.call_count == 2  # Two commits deleted


def test_delete_repository_not_found(mock_firestore_client):
    """Test delete_repository returns False when repository not found."""
    mock_collection = MagicMock()
    mock_repo_doc_ref = MagicMock()
    mock_repo_doc = MagicMock()
    mock_repo_doc.exists = False
    mock_repo_doc_ref.get.return_value = mock_repo_doc
    
    mock_collection.document.return_value = mock_repo_doc_ref
    mock_firestore_client.collection.return_value = mock_collection
    
    db = FirestoreAuditDB()
    result = db.delete_repository("nonexistent/repo")
    
    assert result is False
