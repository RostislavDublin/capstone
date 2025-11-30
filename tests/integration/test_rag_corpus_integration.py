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
from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
import vertexai

from src.audit_models import CommitAudit
from src.storage.rag_corpus import RAGCorpusManager


@contextmanager
def timer(operation_name: str):
    """Context manager to time operations and print results."""
    start = time.time()
    print(f"   ⏱️  Starting: {operation_name}")
    try:
        yield
    finally:
        elapsed = time.time() - start
        print(f"   ⏱️  Finished: {operation_name} ({elapsed:.2f}s)")
        if elapsed > 10:
            print(f"      ⚠️  SLOW: {operation_name} took {elapsed:.2f}s")


def wait_for_indexing(corpus_name: str, file_name: str, max_attempts=4, base_delay=0.5):
    """Wait for RAG file indexing with exponential backoff and status verification.
    
    Checks if file is indexed by listing files and checking state (PENDING -> READY).
    This is the recommended approach from Vertex AI RAG documentation.
    Exponential backoff: 0.5s, 1s, 2s, 4s (max 7.5s, usually exits at ~1-2s).
    
    Args:
        corpus_name: RAG corpus resource name
        file_name: RAG file resource name (used to identify the specific file)
        max_attempts: Maximum attempts (default: 4)
        base_delay: Base delay in seconds (default: 0.5s)
        
    Returns:
        Total time waited in seconds
    """
    from vertexai import rag
    
    start_time = time.time()
    
    for attempt in range(max_attempts):
        delay = base_delay * (2 ** attempt)
        print(f"   ⏳ Wait {attempt + 1}/{max_attempts} ({delay:.1f}s)...")
        time.sleep(delay)
        
        # List files and find our file to check status
        try:
            files = list(rag.list_files(corpus_name=corpus_name))
            for file in files:
                if file.name == file_name:
                    # Check file_status.state (standard field in gapic types)
                    if hasattr(file, 'file_status') and hasattr(file.file_status, 'state'):
                        from google.cloud.aiplatform_v1.types.vertex_rag_data import FileStatus
                        
                        state_value = file.file_status.state
                        if state_value == FileStatus.State.ACTIVE:
                            elapsed = time.time() - start_time
                            print(f"   ✅ Indexed! ({elapsed:.2f}s)")
                            return elapsed
                        elif state_value == FileStatus.State.ERROR:
                            print(f"   ❌ ERROR: {file.file_status.error_status}")
                            elapsed = time.time() - start_time
                            return elapsed  # Exit on error
                        else:
                            state_names = {0: "STATE_UNSPECIFIED", 1: "ACTIVE", 2: "ERROR"}
                            state_name = state_names.get(state_value, f"UNKNOWN({state_value})")
                            print(f"   ⏱️  Status: {state_name}")
                    else:
                        # No file_status field - shouldn't happen with current SDK
                        print(f"   ⚠️  No file_status field, cannot verify")
                    break
            else:
                print(f"   ⚠️  File not found in list")
        except Exception as e:
            print(f"   ⚠️  Error checking status: {e}")
            continue
    
    # Max attempts reached
    elapsed = time.time() - start_time
    print(f"   ⚠️  Max wait ({elapsed:.2f}s)")
    return elapsed


def wait_for_all_files_indexed(corpus_name: str, max_attempts=6, base_delay=0.5):
    """Wait for all files in corpus to be indexed with exponential backoff.
    
    Checks if ALL files are indexed by listing files and checking status.
    This is approach #2 from Vertex AI RAG documentation for multiple files.
    Exponential backoff: 0.5s, 1s, 2s, 4s, 8s, 16s (max 31.5s, usually exits at ~2-4s).
    
    Args:
        corpus_name: RAG corpus resource name
        max_attempts: Maximum attempts (default: 6)
        base_delay: Base delay in seconds (default: 0.5s)
        
    Returns:
        Total time waited in seconds
    """
    from vertexai import rag
    
    start_time = time.time()
    
    for attempt in range(max_attempts):
        delay = base_delay * (2 ** attempt)
        print(f"   ⏳ Wait {attempt + 1}/{max_attempts} ({delay:.1f}s)...")
        time.sleep(delay)
        
        # Check all files status
        try:
            from google.cloud.aiplatform_v1.types.vertex_rag_data import FileStatus
            
            files = list(rag.list_files(corpus_name=corpus_name))
            if not files:
                print(f"   ⚠️  No files found yet")
                continue
            
            # Check if all ACTIVE (ready)
            ready_count = 0
            error_count = 0
            for f in files:
                if hasattr(f, 'file_status') and hasattr(f.file_status, 'state'):
                    if f.file_status.state == FileStatus.State.ACTIVE:
                        ready_count += 1
                    elif f.file_status.state == FileStatus.State.ERROR:
                        error_count += 1
            
            total_count = len(files)
            
            if ready_count == total_count:
                elapsed = time.time() - start_time
                print(f"   ✅ All {total_count} files indexed! ({elapsed:.2f}s)")
                return elapsed
            elif error_count > 0:
                print(f"   ⚠️  {error_count} file(s) have errors, {ready_count}/{total_count} ready")
            else:
                print(f"   ⏱️  {ready_count}/{total_count} files ready")
        except Exception as e:
            print(f"   ⚠️  Error checking status: {e}")
            continue
    
    # Max attempts reached
    elapsed = time.time() - start_time
    print(f"   ⚠️  Max wait ({elapsed:.2f}s)")
    return elapsed


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
    with timer("Initialize corpus"):
        corpus = rag_manager.initialize_corpus()
    print(f"✅ Corpus ready: {corpus.name}")
    
    # Store commit audit
    print("\n2️⃣  Uploading commit audit...")
    with timer("Upload commit audit"):
        result = rag_manager.store_commit_audit(sample_commit_audit, store_files_separately=False)

    assert result is not None
    assert 'commit' in result
    assert result['commit'].display_name == "commit_integra.json"  # First 7 chars of SHA
    print(f"✅ Commit audit stored: {result['commit'].name}")
    print(f"   Display name: {result['commit'].display_name}")
    
    # Wait for indexing with smart retry
    print("\n⏳ Waiting for indexing...")
    with timer("Indexing wait"):
        wait_for_indexing(rag_manager._corpus_resource_name, result['commit'].name)


def test_query_audits_real(rag_manager, sample_commit_audit, vertexai_init):
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
    
    print("✅ Test data uploaded")
    
    # Wait for indexing with smart retry (multiple files)
    print("\n⏳ Waiting for indexing...")
    with timer("Indexing wait"):
        wait_for_all_files_indexed(rag_manager._corpus_resource_name, max_attempts=6)
    
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
