"""Unit tests for RAG Corpus Storage Manager."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from vertexai.preview import rag

from src.audit_models import CommitAudit, RepositoryAudit
from src.storage.rag_corpus import RAGCorpusManager


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_vertexai():
    """Mock vertexai.init to prevent actual GCP calls."""
    with patch("vertexai.init"):
        yield


@pytest.fixture
def mock_rag_corpus():
    """Mock RAG Corpus object."""
    corpus = Mock(spec=rag.RagCorpus)
    corpus.name = "projects/test-project/locations/us-central1/ragCorpora/test-corpus"
    corpus.display_name = "quality-guardian-audits"
    return corpus


@pytest.fixture
def mock_rag_file():
    """Mock RAG File object."""
    rag_file = Mock(spec=rag.RagFile)
    rag_file.name = "projects/test-project/locations/us-central1/ragCorpora/test-corpus/ragFiles/file-123"
    rag_file.display_name = "commit_abc1234.json"
    return rag_file


@pytest.fixture
def sample_commit_audit():
    """Sample CommitAudit for testing."""
    return CommitAudit(
        commit_sha="abc1234567890",
        commit_message="Add user authentication",
        author="John Doe",
        author_email="john@acme.com",
        date=datetime(2025, 11, 21, 10, 0, 0, tzinfo=timezone.utc),
        files_changed=["src/auth.py", "tests/test_auth.py"],
        security_issues=[
            {
                "file": "src/auth.py",
                "line": 42,
                "severity": "HIGH",
                "type": "hardcoded-password",
                "description": "Hardcoded credentials detected",
            }
        ],
        security_score=85.0,
        complexity_issues=[
            {
                "file": "src/auth.py",
                "function": "authenticate",
                "complexity": 15,
                "recommendation": "Break into smaller functions",
            }
        ],
        avg_complexity=8.5,
        max_complexity=15.0,
        total_issues=2,
        critical_issues=0,
        high_issues=1,
        medium_issues=1,
        low_issues=0,
        quality_score=75.0,
    )


@pytest.fixture
def sample_repository_audit():
    """Sample RepositoryAudit for testing."""
    return RepositoryAudit(
        repo_identifier="acme/web-app",
        repo_name="web-app",
        default_branch="main",
        audit_id="audit-123",
        audit_date=datetime(2025, 11, 21, 10, 0, 0, tzinfo=timezone.utc),
        scan_type="bootstrap_full",
        commits_scanned=10,
        date_range_start=datetime(2025, 11, 1, tzinfo=timezone.utc),
        date_range_end=datetime(2025, 11, 21, tzinfo=timezone.utc),
        commit_audits=[],
        total_issues=15,
        critical_issues=0,
        high_issues=2,
        medium_issues=5,
        low_issues=8,
        issues_by_type={"security": 2, "complexity": 5, "style": 8},
        avg_quality_score=82.0,
        quality_trend="stable",
        processing_time=45.2,
    )


@pytest.fixture
def rag_manager():
    """RAG Corpus Manager instance."""
    return RAGCorpusManager(corpus_name="quality-guardian-audits")


# ============================================================================
# Test: Initialization
# ============================================================================


def test_init_default_params(mock_vertexai):
    """Test RAGCorpusManager initialization with default parameters."""
    manager = RAGCorpusManager(corpus_name="test-corpus")

    assert manager.corpus_name == "test-corpus"
    assert manager.corpus_description == "Quality Guardian audit storage: test-corpus"
    assert manager.chunk_size == 512
    assert manager.chunk_overlap == 100
    assert manager._corpus is None
    assert manager._corpus_resource_name is None


def test_init_custom_params(mock_vertexai):
    """Test RAGCorpusManager initialization with custom parameters."""
    manager = RAGCorpusManager(
        corpus_name="custom-corpus",
        corpus_description="Custom description",
        chunk_size=1024,
        chunk_overlap=200,
    )

    assert manager.corpus_name == "custom-corpus"
    assert manager.corpus_description == "Custom description"
    assert manager.chunk_size == 1024
    assert manager.chunk_overlap == 200


# ============================================================================
# Test: Corpus Creation
# ============================================================================


@patch("src.storage.rag_corpus.rag.create_corpus")
@patch("src.storage.rag_corpus.rag.list_corpora")
def test_initialize_corpus_creates_new(
    mock_list_corpora, mock_create_corpus, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test initialize_corpus creates new corpus if none exists."""
    # Mock no existing corpora
    mock_list_corpora.return_value = []
    mock_create_corpus.return_value = mock_rag_corpus

    result = rag_manager.initialize_corpus()

    assert result == mock_rag_corpus
    assert rag_manager._corpus == mock_rag_corpus
    assert rag_manager._corpus_resource_name == mock_rag_corpus.name
    mock_create_corpus.assert_called_once_with(
        display_name="quality-guardian-audits",
        description="Quality Guardian audit storage: quality-guardian-audits",
    )


@patch("src.storage.rag_corpus.rag.create_corpus")
@patch("src.storage.rag_corpus.rag.list_corpora")
def test_initialize_corpus_finds_existing(
    mock_list_corpora, mock_create_corpus, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test initialize_corpus finds and returns existing corpus."""
    # Mock existing corpus
    mock_list_corpora.return_value = [mock_rag_corpus]

    result = rag_manager.initialize_corpus()

    assert result == mock_rag_corpus
    assert rag_manager._corpus == mock_rag_corpus
    assert rag_manager._corpus_resource_name == mock_rag_corpus.name
    mock_create_corpus.assert_not_called()


@patch("src.storage.rag_corpus.rag.list_corpora")
def test_initialize_corpus_idempotent(
    mock_list_corpora, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test initialize_corpus is idempotent (doesn't create duplicate)."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name

    result = rag_manager.initialize_corpus()

    assert result == mock_rag_corpus
    mock_list_corpora.assert_not_called()


@patch("src.storage.rag_corpus.rag.create_corpus")
@patch("src.storage.rag_corpus.rag.list_corpora")
def test_initialize_corpus_create_failure(
    mock_list_corpora, mock_create_corpus, mock_vertexai, rag_manager
):
    """Test initialize_corpus raises error on creation failure."""
    mock_list_corpora.return_value = []
    mock_create_corpus.side_effect = Exception("API Error")

    with pytest.raises(RuntimeError, match="Failed to create corpus"):
        rag_manager.initialize_corpus()


# ============================================================================
# Test: Store Commit Audit
# ============================================================================


@patch("src.storage.rag_corpus.rag.upload_file")
@patch("src.storage.rag_corpus.Path")
def test_store_commit_audit_success(
    mock_path,
    mock_upload_file,
    mock_vertexai,
    rag_manager,
    sample_commit_audit,
    mock_rag_corpus,
    mock_rag_file,
):
    """Test store_commit_audit successfully uploads audit."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name
    mock_upload_file.return_value = mock_rag_file

    # Mock temp file cleanup
    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.exists.return_value = True

    result = rag_manager.store_commit_audit(sample_commit_audit, store_files_separately=False)

    assert result['commit'] == mock_rag_file
    mock_upload_file.assert_called_once()

    # Check call arguments
    call_args = mock_upload_file.call_args
    assert call_args.kwargs["corpus_name"] == mock_rag_corpus.name
    assert call_args.kwargs["display_name"] == "commit_abc1234.json"
    assert "Commit audit:" in call_args.kwargs["description"]


@patch("src.storage.rag_corpus.rag.upload_file")
def test_store_commit_audit_custom_display_name(
    mock_upload_file,
    mock_vertexai,
    rag_manager,
    sample_commit_audit,
    mock_rag_corpus,
    mock_rag_file,
):
    """Test store_commit_audit with custom display name."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name
    mock_upload_file.return_value = mock_rag_file

    result = rag_manager.store_commit_audit(
        sample_commit_audit, display_name="custom_name.json", store_files_separately=False
    )

    assert result['commit'] == mock_rag_file
    call_args = mock_upload_file.call_args
    assert call_args.kwargs["display_name"] == "custom_name.json"


def test_store_commit_audit_without_init(mock_vertexai, rag_manager, sample_commit_audit):
    """Test store_commit_audit raises error if corpus not initialized."""
    with pytest.raises(RuntimeError, match="Corpus not initialized"):
        rag_manager.store_commit_audit(sample_commit_audit)


@patch("src.storage.rag_corpus.rag.upload_file")
def test_store_commit_audit_upload_failure(
    mock_upload_file,
    mock_vertexai,
    rag_manager,
    sample_commit_audit,
    mock_rag_corpus,
):
    """Test store_commit_audit raises error on upload failure."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name
    mock_upload_file.side_effect = Exception("Upload failed")

    with pytest.raises(RuntimeError, match="Failed to upload file"):
        rag_manager.store_commit_audit(sample_commit_audit)


# ============================================================================
# Test: Store Repository Audit
# ============================================================================


@patch("src.storage.rag_corpus.rag.upload_file")
@patch("src.storage.rag_corpus.Path")
def test_store_repository_audit_success(
    mock_path,
    mock_upload_file,
    mock_vertexai,
    rag_manager,
    sample_repository_audit,
    mock_rag_corpus,
    mock_rag_file,
):
    """Test store_repository_audit successfully uploads audit."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name
    mock_upload_file.return_value = mock_rag_file

    # Mock temp file cleanup
    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.exists.return_value = True

    result = rag_manager.store_repository_audit(sample_repository_audit)

    assert result == mock_rag_file
    mock_upload_file.assert_called_once()

    # Check call arguments
    call_args = mock_upload_file.call_args
    assert call_args.kwargs["corpus_name"] == mock_rag_corpus.name
    assert call_args.kwargs["display_name"] == "repo_web-app.json"
    assert "Repository audit:" in call_args.kwargs["description"]
    assert "10 commits" in call_args.kwargs["description"]


def test_store_repository_audit_without_init(
    mock_vertexai, rag_manager, sample_repository_audit
):
    """Test store_repository_audit raises error if corpus not initialized."""
    with pytest.raises(RuntimeError, match="Corpus not initialized"):
        rag_manager.store_repository_audit(sample_repository_audit)


# ============================================================================
# Test: Query Audits
# ============================================================================


@patch("src.storage.rag_corpus.rag.retrieval_query")
def test_query_audits_success(
    mock_retrieval_query, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test query_audits returns results successfully."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name

    # Mock response
    mock_context1 = Mock()
    mock_context1.text = "Audit result 1"
    mock_context1.distance = 0.85
    mock_context1.source_uri = "gs://bucket/file1.json"

    mock_context2 = Mock()
    mock_context2.text = "Audit result 2"
    mock_context2.distance = 0.72
    mock_context2.source_uri = "gs://bucket/file2.json"

    mock_contexts = Mock()
    mock_contexts.contexts = [mock_context1, mock_context2]

    mock_response = Mock()
    mock_response.contexts = mock_contexts

    mock_retrieval_query.return_value = mock_response

    results = rag_manager.query_audits("Show security issues", top_k=5)

    assert len(results) == 2
    assert results[0]["text"] == "Audit result 1"
    assert abs(results[0]["distance"] - 0.85) < 0.01
    assert results[1]["text"] == "Audit result 2"

    mock_retrieval_query.assert_called_once()
    call_args = mock_retrieval_query.call_args
    assert call_args.kwargs["text"] == "Show security issues"
    assert call_args.kwargs["similarity_top_k"] == 5


@patch("src.storage.rag_corpus.rag.retrieval_query")
def test_query_audits_with_threshold(
    mock_retrieval_query, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test query_audits with vector distance threshold."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name

    mock_contexts = Mock()
    mock_contexts.contexts = []
    mock_response = Mock()
    mock_response.contexts = mock_contexts
    mock_retrieval_query.return_value = mock_response

    rag_manager.query_audits("test query", vector_distance_threshold=0.8)

    call_args = mock_retrieval_query.call_args
    assert abs(call_args.kwargs["vector_distance_threshold"] - 0.8) < 0.01


def test_query_audits_without_init(mock_vertexai, rag_manager):
    """Test query_audits raises error if corpus not initialized."""
    with pytest.raises(RuntimeError, match="Corpus not initialized"):
        rag_manager.query_audits("test query")


@patch("src.storage.rag_corpus.rag.retrieval_query")
def test_query_audits_empty_results(
    mock_retrieval_query, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test query_audits handles empty results."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name

    mock_response = Mock()
    mock_response.contexts = None
    mock_retrieval_query.return_value = mock_response

    results = rag_manager.query_audits("non-existent query")

    assert results == []


@patch("src.storage.rag_corpus.rag.retrieval_query")
def test_query_audits_failure(
    mock_retrieval_query, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test query_audits raises error on query failure."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name
    mock_retrieval_query.side_effect = Exception("Query failed")

    with pytest.raises(RuntimeError, match="Query failed"):
        rag_manager.query_audits("test query")


# ============================================================================
# Test: Get Latest Audit
# ============================================================================


@patch("src.storage.rag_corpus.rag.retrieval_query")
def test_get_latest_audit_found(
    mock_retrieval_query, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test get_latest_audit returns latest audit."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name

    mock_context = Mock()
    mock_context.text = "Latest audit"
    mock_context.distance = 0.95

    mock_contexts = Mock()
    mock_contexts.contexts = [mock_context]

    mock_response = Mock()
    mock_response.contexts = mock_contexts
    mock_retrieval_query.return_value = mock_response

    result = rag_manager.get_latest_audit("acme/web-app", audit_type="commit")

    assert result is not None
    assert result["text"] == "Latest audit"


@patch("src.storage.rag_corpus.rag.retrieval_query")
def test_get_latest_audit_not_found(
    mock_retrieval_query, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test get_latest_audit returns None when no audit found."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name

    mock_response = Mock()
    mock_response.contexts = None
    mock_retrieval_query.return_value = mock_response

    result = rag_manager.get_latest_audit("acme/web-app")

    assert result is None


def test_get_latest_audit_without_init(mock_vertexai, rag_manager):
    """Test get_latest_audit raises error if corpus not initialized."""
    with pytest.raises(RuntimeError, match="Corpus not initialized"):
        rag_manager.get_latest_audit("acme/web-app")


# ============================================================================
# Test: Delete Corpus
# ============================================================================


@patch("src.storage.rag_corpus.rag.delete_corpus")
def test_delete_corpus_success(
    mock_delete_corpus, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test delete_corpus successfully deletes corpus."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name

    rag_manager.delete_corpus()

    mock_delete_corpus.assert_called_once_with(name=mock_rag_corpus.name)
    assert rag_manager._corpus is None
    assert rag_manager._corpus_resource_name is None


@patch("src.storage.rag_corpus.rag.delete_corpus")
def test_delete_corpus_not_initialized(mock_delete_corpus, mock_vertexai, rag_manager):
    """Test delete_corpus handles case when corpus not initialized."""
    rag_manager.delete_corpus()

    mock_delete_corpus.assert_not_called()


@patch("src.storage.rag_corpus.rag.delete_corpus")
def test_delete_corpus_failure(
    mock_delete_corpus, mock_vertexai, rag_manager, mock_rag_corpus
):
    """Test delete_corpus raises error on deletion failure."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name
    mock_delete_corpus.side_effect = Exception("Delete failed")

    with pytest.raises(RuntimeError, match="Failed to delete corpus"):
        rag_manager.delete_corpus()


# ============================================================================
# Test: Temp File Cleanup
# ============================================================================


@patch("src.storage.rag_corpus.rag.upload_file")
@patch("src.storage.rag_corpus.Path")
def test_temp_file_cleanup_on_success(
    mock_path,
    mock_upload_file,
    mock_vertexai,
    rag_manager,
    sample_commit_audit,
    mock_rag_corpus,
    mock_rag_file,
):
    """Test temporary file is cleaned up after successful upload."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name
    mock_upload_file.return_value = mock_rag_file

    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.exists.return_value = True

    rag_manager.store_commit_audit(sample_commit_audit)

    mock_path_instance.unlink.assert_called_once()


@patch("src.storage.rag_corpus.rag.upload_file")
@patch("src.storage.rag_corpus.Path")
def test_temp_file_cleanup_on_failure(
    mock_path,
    mock_upload_file,
    mock_vertexai,
    rag_manager,
    sample_commit_audit,
    mock_rag_corpus,
):
    """Test temporary file is cleaned up even after upload failure."""
    rag_manager._corpus = mock_rag_corpus
    rag_manager._corpus_resource_name = mock_rag_corpus.name
    mock_upload_file.side_effect = Exception("Upload failed")

    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.exists.return_value = True

    with pytest.raises(RuntimeError):
        rag_manager.store_commit_audit(sample_commit_audit)

    mock_path_instance.unlink.assert_called_once()
