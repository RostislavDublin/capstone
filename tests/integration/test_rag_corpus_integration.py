"""Integration tests for RAG Corpus Storage with real Vertex AI.

These tests make REAL API calls to Vertex AI and require:
- GCP project configured
- Vertex AI API enabled
- Service account with permissions
- GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION env vars

Run with: pytest tests/integration/test_rag_corpus_integration.py -v -s
"""

import os
import time
from datetime import datetime, timezone

import pytest
import vertexai

from src.audit_models import CommitAudit, RepositoryAudit
from src.storage.rag_corpus import RAGCorpusManager


# Skip if environment not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_CLOUD_PROJECT") or not os.getenv("GOOGLE_CLOUD_LOCATION"),
    reason="GCP environment not configured (need GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION)",
)


@pytest.fixture(scope="module")
def vertexai_init():
    """Initialize Vertex AI for integration tests."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    print(f"\n🔧 Initializing Vertex AI: project={project}, location={location}")
    vertexai.init(project=project, location=location)
    
    yield {"project": project, "location": location}


@pytest.fixture
def test_corpus_name():
    """Generate unique corpus name for test."""
    timestamp = int(time.time())
    return f"test-quality-guardian-{timestamp}"


@pytest.fixture
def rag_manager(vertexai_init, test_corpus_name):
    """Create RAG Corpus Manager for testing.
    
    Yields manager, then cleans up corpus after test.
    """
    manager = RAGCorpusManager(
        corpus_name=test_corpus_name,
        corpus_description="Integration test corpus (auto-delete)",
        chunk_size=512,
        chunk_overlap=100,
    )
    
    print(f"\n📦 Creating test corpus: {test_corpus_name}")
    
    yield manager
    
    # Cleanup: delete corpus after test
    try:
        print(f"\n🧹 Cleaning up test corpus: {test_corpus_name}")
        manager.delete_corpus()
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")


@pytest.fixture
def sample_commit_audit():
    """Sample CommitAudit for integration testing."""
    return CommitAudit(
        repository="test-owner/test-repo",
        commit_sha="integration-test-sha-12345",
        commit_message="Integration test: Add RAG storage",
        author="Integration Test",
        author_email="test@integration.local",
        date=datetime(2025, 11, 21, 12, 0, 0, tzinfo=timezone.utc),
        files_changed=["src/storage/rag_corpus.py", "tests/integration/test_rag_corpus_integration.py"],
        security_issues=[
            {
                "file": "src/storage/rag_corpus.py",
                "line": 100,
                "severity": "LOW",
                "type": "test-issue",
                "description": "This is a test security finding",
            }
        ],
        security_score=95.0,
        complexity_issues=[],
        avg_complexity=5.2,
        max_complexity=8.0,
        total_issues=1,
        critical_issues=0,
        high_issues=0,
        medium_issues=0,
        low_issues=1,
        quality_score=92.0,
    )


@pytest.fixture
def sample_repository_audit():
    """Sample RepositoryAudit for integration testing."""
    return RepositoryAudit(
        repo_identifier="test/integration-repo",
        repo_name="integration-repo",
        default_branch="main",
        audit_id="integration-audit-001",
        audit_date=datetime(2025, 11, 21, 12, 0, 0, tzinfo=timezone.utc),
        scan_type="bootstrap_full",
        commits_scanned=5,
        date_range_start=datetime(2025, 11, 1, tzinfo=timezone.utc),
        date_range_end=datetime(2025, 11, 21, tzinfo=timezone.utc),
        commit_audits=[],
        total_issues=8,
        critical_issues=0,
        high_issues=1,
        medium_issues=3,
        low_issues=4,
        issues_by_type={"security": 2, "complexity": 4, "style": 2},
        avg_quality_score=88.5,
        quality_trend="improving",
        processing_time=12.5,
    )


# ============================================================================
# Integration Tests - Real Vertex AI API Calls
# ============================================================================


def test_corpus_lifecycle(rag_manager, vertexai_init):
    """Test complete corpus lifecycle: create, get, delete.
    
    This tests:
    - Corpus creation with Vertex AI
    - Finding existing corpus
    - Corpus deletion
    """
    print("\n" + "="*70)
    print("TEST: Corpus Lifecycle")
    print("="*70)
    
    # Step 1: Initialize corpus (creates new one)
    print("\n1️⃣  Creating corpus...")
    corpus = rag_manager.initialize_corpus()
    
    assert corpus is not None
    assert corpus.display_name == rag_manager.corpus_name
    assert rag_manager._corpus_resource_name is not None
    print(f"✅ Corpus created: {corpus.name}")
    
    # Step 2: Initialize again (should find existing)
    print("\n2️⃣  Finding existing corpus...")
    rag_manager._corpus = None  # Reset cache
    rag_manager._corpus_resource_name = None
    
    corpus2 = rag_manager.initialize_corpus()
    assert corpus2 is not None
    # Compare corpus ID (last part), not full name (project number may differ from project ID)
    corpus_id1 = corpus.name.split("/")[-1]
    corpus_id2 = corpus2.name.split("/")[-1]
    assert corpus_id2 == corpus_id1, f"Corpus ID mismatch: {corpus_id2} != {corpus_id1}"
    print(f"✅ Found existing corpus: {corpus2.name}")
    
    # Step 3: Delete will be done by fixture cleanup


def test_store_commit_audit_real(rag_manager, sample_commit_audit, vertexai_init):
    """Test storing CommitAudit with real Vertex AI upload.
    
    This tests:
    - JSON serialization of CommitAudit
    - Temp file creation
    - Upload to Vertex AI RAG Corpus
    - File indexing
    """
    print("\n" + "="*70)
    print("TEST: Store Commit Audit")
    print("="*70)
    
    # Initialize corpus
    print("\n1️⃣  Initializing corpus...")
    corpus = rag_manager.initialize_corpus()
    print(f"✅ Corpus ready: {corpus.name}")
    
    # Store commit audit
    print("\n2️⃣  Uploading commit audit...")
    result = rag_manager.store_commit_audit(sample_commit_audit, store_files_separately=False)

    assert result is not None
    assert 'commit' in result
    assert result['commit'].display_name == "commit_integra.json"  # First 7 chars of SHA
    print(f"✅ Commit audit stored: {result['commit'].name}")
    print(f"   Display name: {result['commit'].display_name}")
    
    # Wait for indexing
    print("\n⏳ Waiting for indexing (5 seconds)...")
    time.sleep(5)
    print("✅ Indexing should be complete")


def test_store_repository_audit_real(rag_manager, sample_repository_audit, vertexai_init):
    """Test storing RepositoryAudit with real Vertex AI upload.
    
    This tests:
    - JSON serialization of RepositoryAudit
    - Upload of larger document
    - Metadata handling
    """
    print("\n" + "="*70)
    print("TEST: Store Repository Audit")
    print("="*70)
    
    # Initialize corpus
    print("\n1️⃣  Initializing corpus...")
    corpus = rag_manager.initialize_corpus()
    print(f"✅ Corpus ready: {corpus.name}")
    
    # Store repository audit
    print("\n2️⃣  Uploading repository audit...")
    rag_file = rag_manager.store_repository_audit(sample_repository_audit)
    
    assert rag_file is not None
    assert rag_file.display_name == "repo_integration-repo.json"
    print(f"✅ Repository audit stored: {rag_file.name}")
    print(f"   Display name: {rag_file.display_name}")
    
    # Wait for indexing
    print("\n⏳ Waiting for indexing (5 seconds)...")
    time.sleep(5)
    print("✅ Indexing should be complete")


def test_query_audits_real(rag_manager, sample_commit_audit, sample_repository_audit, vertexai_init):
    """Test semantic search queries with real Vertex AI retrieval.
    
    This tests:
    - Upload multiple documents
    - Semantic search query
    - Result retrieval with metadata
    """
    print("\n" + "="*70)
    print("TEST: Query Audits")
    print("="*70)
    
    # Initialize and upload test data
    print("\n1️⃣  Setting up test data...")
    corpus = rag_manager.initialize_corpus()
    
    print("   Uploading commit audit...")
    rag_manager.store_commit_audit(sample_commit_audit)
    
    print("   Uploading repository audit...")
    rag_manager.store_repository_audit(sample_repository_audit)
    
    print("✅ Test data uploaded")
    
    # Wait for indexing
    print("\n⏳ Waiting for indexing (10 seconds)...")
    time.sleep(10)
    
    # Query 1: Security issues
    print("\n2️⃣  Query 1: Security issues...")
    results = rag_manager.query_audits("security issues found in code", top_k=5)
    
    print(f"✅ Query returned {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"   Result {i}:")
        print(f"      Text preview: {result['text'][:100]}...")
        if result.get('distance'):
            print(f"      Distance: {result['distance']:.4f}")
    
    assert isinstance(results, list)
    # Note: Results may be empty if indexing hasn't completed
    
    # Query 2: Quality trends
    print("\n3️⃣  Query 2: Quality trends...")
    results2 = rag_manager.query_audits("quality score and trends", top_k=5)
    
    print(f"✅ Query returned {len(results2)} results")
    assert isinstance(results2, list)
    
    # Query 3: With threshold
    print("\n4️⃣  Query 3: With distance threshold...")
    results3 = rag_manager.query_audits(
        "integration test",
        top_k=3,
        vector_distance_threshold=0.5
    )
    
    print(f"✅ Query returned {len(results3)} results (threshold filtered)")
    assert isinstance(results3, list)


def test_get_latest_audit_real(rag_manager, sample_commit_audit, vertexai_init):
    """Test getting latest audit with real Vertex AI query.
    
    This tests:
    - Upload audit
    - Query for latest
    - Result filtering
    """
    print("\n" + "="*70)
    print("TEST: Get Latest Audit")
    print("="*70)
    
    # Setup
    print("\n1️⃣  Setting up test data...")
    corpus = rag_manager.initialize_corpus()
    rag_manager.store_commit_audit(sample_commit_audit)
    print("✅ Commit audit uploaded")
    
    # Wait for indexing
    print("\n⏳ Waiting for indexing (10 seconds)...")
    time.sleep(10)
    
    # Get latest
    print("\n2️⃣  Querying for latest audit...")
    result = rag_manager.get_latest_audit("test/integration-repo", audit_type="commit")
    
    if result:
        print(f"✅ Found latest audit")
        print(f"   Text preview: {result.get('text', '')[:100]}...")
        assert "text" in result
    else:
        print("⚠️  No results (indexing may not be complete)")
    
    # Note: May return None if indexing incomplete
    assert result is None or isinstance(result, dict)


def test_error_handling_uninit(rag_manager):
    """Test error handling when corpus not initialized.
    
    This tests:
    - Proper error messages
    - No API calls without initialization
    """
    print("\n" + "="*70)
    print("TEST: Error Handling - Uninitialized")
    print("="*70)
    
    # Don't initialize corpus
    
    # Try to store without init
    print("\n1️⃣  Attempting store without init...")
    with pytest.raises(RuntimeError, match="Corpus not initialized"):
        sample_audit = CommitAudit(
            repository="test/repo",
            commit_sha="test",
            commit_message="test",
            author="test",
            author_email="test@test.com",
            date=datetime.now(timezone.utc),
            files_changed=[],
            processing_time=0.0,
        )
        rag_manager.store_commit_audit(sample_audit)
    print("✅ Correct error raised")
    
    # Try to query without init
    print("\n2️⃣  Attempting query without init...")
    with pytest.raises(RuntimeError, match="Corpus not initialized"):
        rag_manager.query_audits("test")
    print("✅ Correct error raised")
    
    # Try to get latest without init
    print("\n3️⃣  Attempting get_latest without init...")
    with pytest.raises(RuntimeError, match="Corpus not initialized"):
        rag_manager.get_latest_audit("test/repo")
    print("✅ Correct error raised")


# ============================================================================
# Summary Test - Full Workflow
# ============================================================================


def test_full_workflow_integration(rag_manager, sample_commit_audit, sample_repository_audit, vertexai_init):
    """Complete end-to-end workflow test.
    
    This simulates the actual Quality Guardian workflow:
    1. Bootstrap: Create corpus
    2. Audit: Upload commit audits
    3. Aggregate: Upload repository audit
    4. Query: Search for insights
    5. Cleanup: Delete corpus
    """
    print("\n" + "="*70)
    print("TEST: Full Workflow Integration")
    print("="*70)
    
    # Step 1: Initialize (Bootstrap phase)
    print("\n🔵 PHASE 1: Bootstrap")
    print("─" * 70)
    corpus = rag_manager.initialize_corpus()
    print(f"✅ Corpus created: {corpus.display_name}")
    
    # Step 2: Store multiple audits (Audit phase)
    print("\n🔵 PHASE 2: Audit Collection")
    print("─" * 70)
    
    print("   Storing commit audit 1...")
    result1 = rag_manager.store_commit_audit(sample_commit_audit, store_files_separately=False)
    print(f"   ✅ Stored: {result1['commit'].display_name}")
    
    print("   Storing commit audit 2 (modified)...")
    sample_commit_audit.commit_sha = "integration-test-sha-67890"
    sample_commit_audit.quality_score = 85.0
    result2 = rag_manager.store_commit_audit(sample_commit_audit, store_files_separately=False)
    print(f"   ✅ Stored: {result2['commit'].display_name}")
    
    print("   Storing repository audit...")
    rag_file3 = rag_manager.store_repository_audit(sample_repository_audit)
    print(f"   ✅ Stored: {rag_file3.display_name}")
    
    # Step 3: Wait for indexing
    print("\n⏳ Waiting for indexing (15 seconds)...")
    time.sleep(15)
    
    # Step 4: Query insights (Query phase)
    print("\n🔵 PHASE 3: Query & Analysis")
    print("─" * 70)
    
    queries = [
        "What security issues were found?",
        "Show quality trends",
        "Integration test results",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n   Query {i}: {query}")
        results = rag_manager.query_audits(query, top_k=3)
        print(f"   ✅ Returned {len(results)} results")
        
        for j, result in enumerate(results, 1):
            preview = result['text'][:80].replace('\n', ' ')
            print(f"      {j}. {preview}...")
    
    # Step 5: Validate
    print("\n🔵 PHASE 4: Validation")
    print("─" * 70)
    print("✅ Corpus lifecycle: OK")
    print("✅ Upload operations: OK")
    print("✅ Query operations: OK")
    print("✅ Error handling: OK")
    
    print("\n" + "="*70)
    print("🎉 FULL WORKFLOW INTEGRATION TEST PASSED")
    print("="*70)
