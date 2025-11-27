"""Integration tests for Firestore client with real Firestore database."""

import pytest
import os
import time
from datetime import datetime

import sys
sys.path.insert(0, 'src')

from storage.firestore_client import FirestoreAuditDB
from audit_models import CommitAudit


# Skip tests if GCP environment not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_CLOUD_PROJECT"),
    reason="GCP environment not configured (need GOOGLE_CLOUD_PROJECT)"
)


@pytest.fixture(scope="module")
def firestore_db():
    """Create Firestore client for integration tests."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    db = FirestoreAuditDB(
        project_id=project_id,
        database="(default)",
        collection_prefix="test-quality-guardian"
    )
    yield db
    
    # Cleanup: delete all test repositories
    repos = db.get_repositories()
    for repo in repos:
        db.delete_repository(repo)


@pytest.fixture
def sample_audit():
    """Sample CommitAudit for testing."""
    return CommitAudit(
        repository="test-org/test-repo",
        commit_sha="abc123def456789",
        commit_message="Test commit for integration testing",
        author="Test Author",
        author_email="test@example.com",
        date=datetime(2024, 11, 26, 10, 0, 0),
        files_changed=["src/main.py", "tests/test_main.py"],
        security_score=95.0,
        quality_score=88.5,
        security_issues=[],
        complexity_issues=[],
        code_quality_issues=[],
        overall_assessment="Test commit with good quality",
    )


def test_store_and_retrieve_commit(firestore_db, sample_audit):
    """Test storing and retrieving a commit audit."""
    # Store commit
    firestore_db.store_commit_audit(sample_audit)
    
    # Wait for Firestore eventual consistency with exponential backoff
    audits = []
    for attempt in range(5):
        audits = firestore_db.query_by_repository("test-org/test-repo", limit=10)
        if len(audits) >= 1:
            break
        time.sleep(0.5 * (2 ** attempt))  # 0.5s, 1s, 2s, 4s, 8s
    
    assert len(audits) >= 1
    retrieved = audits[0]
    assert retrieved.commit_sha == sample_audit.commit_sha
    assert retrieved.repository == sample_audit.repository
    assert retrieved.author == sample_audit.author
    assert retrieved.security_score == sample_audit.security_score


def test_get_repositories(firestore_db, sample_audit):
    """Test listing all repositories."""
    # Store commit
    firestore_db.store_commit_audit(sample_audit)
    
    # Get repositories
    repos = firestore_db.get_repositories()
    
    assert len(repos) >= 1
    assert "test-org/test-repo" in repos


def test_repository_stats(firestore_db, sample_audit):
    """Test getting repository statistics."""
    # Store commit
    firestore_db.store_commit_audit(sample_audit)
    
    # Get stats
    stats = firestore_db.get_repository_stats("test-org/test-repo")
    
    assert stats is not None
    assert stats["name"] == "test-org/test-repo"
    assert stats["total_commits"] >= 1
    assert "first_analyzed" in stats
    assert "last_analyzed" in stats


def test_multiple_commits_same_repo(firestore_db):
    """Test storing multiple commits for the same repository."""
    audits_to_store = [
        CommitAudit(
            repository="test-org/multi-commit",
            commit_sha=f"commit{i:03d}",
            commit_message=f"Commit {i}",
            author="Test Author",
            author_email="test@example.com",
            date=datetime(2024, 11, 26, 10, i, 0),
            files_changed=[f"file{i}.py"],
            security_score=90.0 + i,
            quality_score=85.0 + i,
            security_issues=[],
            complexity_issues=[],
            code_quality_issues=[],
            overall_assessment=f"Test commit {i}",
        )
        for i in range(5)
    ]
    
    # Store all commits
    for audit in audits_to_store:
        firestore_db.store_commit_audit(audit)
    
    # Retrieve commits
    retrieved = firestore_db.query_by_repository(
        "test-org/multi-commit",
        limit=10,
        order_by="date",
        descending=True
    )
    
    assert len(retrieved) == 5
    # Should be ordered by date descending
    assert retrieved[0].commit_sha == "commit004"
    assert retrieved[4].commit_sha == "commit000"
    
    # Check stats
    stats = firestore_db.get_repository_stats("test-org/multi-commit")
    assert stats["total_commits"] == 5


def test_multiple_repositories(firestore_db):
    """Test storing commits for multiple repositories."""
    repos = ["org1/repo1", "org2/repo2", "org3/repo3"]
    
    for repo in repos:
        audit = CommitAudit(
            repository=repo,
            commit_sha=f"{repo.replace('/', '_')}_sha",
            commit_message=f"Commit for {repo}",
            author="Test Author",
            author_email="test@example.com",
            date=datetime(2024, 11, 26, 12, 0, 0),
            files_changed=["main.py"],
            security_score=90.0,
            quality_score=85.0,
            security_issues=[],
            complexity_issues=[],
            code_quality_issues=[],
            overall_assessment="Test commit",
        )
        firestore_db.store_commit_audit(audit)
    
    # Get all repositories
    all_repos = firestore_db.get_repositories()
    
    for repo in repos:
        assert repo in all_repos


def test_delete_repository(firestore_db, sample_audit):
    """Test deleting a repository and its commits."""
    # Store commit
    firestore_db.store_commit_audit(sample_audit)
    
    # Verify it exists
    repos_before = firestore_db.get_repositories()
    assert "test-org/test-repo" in repos_before
    
    # Delete repository
    result = firestore_db.delete_repository("test-org/test-repo")
    assert result is True
    
    # Verify it's gone
    repos_after = firestore_db.get_repositories()
    assert "test-org/test-repo" not in repos_after
    
    # Verify commits are gone
    audits = firestore_db.query_by_repository("test-org/test-repo")
    assert len(audits) == 0


def test_query_with_limit(firestore_db):
    """Test querying with limit parameter."""
    # Store 10 commits
    for i in range(10):
        audit = CommitAudit(
            repository="test-org/limit-test",
            commit_sha=f"sha{i:03d}",
            commit_message=f"Commit {i}",
            author="Test Author",
            author_email="test@example.com",
            date=datetime(2024, 11, 26, 10, i, 0),
            files_changed=["file.py"],
            security_score=90.0,
            quality_score=85.0,
            security_issues=[],
            complexity_issues=[],
            code_quality_issues=[],
            overall_assessment="Test",
        )
        firestore_db.store_commit_audit(audit)
    
    # Wait for Firestore eventual consistency with exponential backoff
    limited = []
    for attempt in range(5):
        limited = firestore_db.query_by_repository("test-org/limit-test", limit=5)
        if len(limited) == 5:
            break
        time.sleep(0.5 * (2 ** attempt))  # 0.5s, 1s, 2s, 4s, 8s
    
    assert len(limited) == 5
    
    # Query without limit
    all_commits = firestore_db.query_by_repository("test-org/limit-test")
    assert len(all_commits) == 10
