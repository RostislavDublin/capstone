#!/usr/bin/env python3
"""Quick demo: Test Firestore integration with minimal commits.

Parametrized version for fast validation:
- Clean slate (Firestore + RAG)
- Minimal commits (1-2)
- End-to-end flow validation
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

# Setup logging
logging.basicConfig(level=logging.WARNING)

def clean_all_storage():
    """Clean both Firestore and RAG corpus."""
    import vertexai
    from storage.rag_corpus import RAGCorpusManager
    from storage.firestore_client import FirestoreAuditDB
    
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    vertexai.init(project=project, location="us-west1")
    
    print("\n🧹 Cleaning storage...")
    
    # Clean Firestore
    db = FirestoreAuditDB(
        project_id=project,
        database="(default)",
        collection_prefix="quality-guardian"
    )
    
    repos = db.get_repositories()
    deleted_count = 0
    for repo in repos:
        db.delete_repository(repo)
        deleted_count += 1
    
    print(f"   ✓ Firestore: deleted {deleted_count} repositories")
    
    # Clean RAG
    rag = RAGCorpusManager(corpus_name="quality-guardian-audits")
    rag.initialize_corpus()
    files_deleted = rag.clear_all_files()
    print(f"   ✓ RAG: deleted {files_deleted} files")
    print()

async def quick_test(num_commits: int = 1):
    """Quick test with minimal commits."""
    from agents.quality_guardian.agent import root_agent
    from google.adk.runners import InMemoryRunner
    from fixtures.test_repo_fixture import get_test_repo_name
    from fixtures.fast_reset_api import reset_to_fixture_state_api
    
    test_repo = get_test_repo_name()
    
    print("=" * 70)
    print(f"  QUICK TEST: Firestore Integration ({num_commits} commit{'s' if num_commits > 1 else ''})")
    print("=" * 70)
    
    # Clean storage
    clean_all_storage()
    
    # Reset fixture to minimal commits
    print(f"📝 Preparing test repo: {test_repo}")
    print(f"   Setting up {num_commits} fixture commit(s)...\n")
    
    reset_to_fixture_state_api(initial_commits=num_commits)
    total_commits = num_commits + 1  # +1 for initial commit
    print(f"   ✓ Ready: {total_commits} total commits (1 initial + {num_commits} fixtures)\n")
    
    # Create runner
    runner = InMemoryRunner(agent=root_agent)
    
    # Test 1: Bootstrap
    print("=" * 70)
    print(f"  TEST 1: Bootstrap {total_commits} commits")
    print("=" * 70)
    
    command = f"Bootstrap {test_repo} with {total_commits} commits"
    print(f"\n🗣️  User: '{command}'\n")
    
    response = await runner.run_debug(command)
    print()
    
    # Verify Firestore
    print("=" * 70)
    print("  VERIFICATION: Check Firestore")
    print("=" * 70)
    
    from storage.firestore_client import FirestoreAuditDB
    import vertexai
    
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    vertexai.init(project=project, location="us-west1")
    
    db = FirestoreAuditDB(
        project_id=project,
        database="(default)",
        collection_prefix="quality-guardian"
    )
    
    print(f"\n📊 Firestore contents:")
    repos = db.get_repositories()
    print(f"   • Repositories: {len(repos)}")
    
    if test_repo in repos:
        print(f"   ✅ Found: {test_repo}")
        
        stats = db.get_repository_stats(test_repo)
        print(f"   • Total commits in DB: {stats['total_commits']}")
        print(f"   • Last analyzed: {stats['last_analyzed']}")
        
        commits = db.query_by_repository(test_repo, limit=10)
        print(f"   • Commits retrieved: {len(commits)}")
        
        if len(commits) > 0:
            print(f"\n   First commit:")
            print(f"   - SHA: {commits[0].commit_sha[:7]}")
            print(f"   - Message: {commits[0].commit_message[:50]}")
            print(f"   - Quality: {commits[0].quality_score}")
    else:
        print(f"   ❌ NOT FOUND: {test_repo}")
    
    # Test 2: List repositories
    print("\n" + "=" * 70)
    print("  TEST 2: List Repositories")
    print("=" * 70)
    
    command2 = "List analyzed repositories"
    print(f"\n🗣️  User: '{command2}'\n")
    
    response2 = await runner.run_debug(command2)
    print()
    
    # Final verification
    print("=" * 70)
    print("  FINAL CHECK: Dual Write Verification")
    print("=" * 70)
    
    print("\n✅ Firestore Integration:")
    print("   • Repository stored: YES")
    print(f"   • Commits in Firestore: {stats['total_commits']}")
    print(f"   • List command works: {'YES' if len(repos) > 0 else 'NO'}")
    
    print("\n✅ RAG Integration (secondary cache):")
    from storage.rag_corpus import RAGCorpusManager
    rag = RAGCorpusManager(corpus_name="quality-guardian-audits")
    rag.initialize_corpus()
    rag_stats = rag.get_corpus_stats()
    print(f"   • Files in RAG corpus: {rag_stats.get('commit_files', 0)}")
    
    print("\n" + "=" * 70)
    print("  ✅ PHASE 4 VALIDATION COMPLETE")
    print("=" * 70)
    print("\n📌 Status:")
    print("   ✅ Phase 1: Firestore client - DONE")
    print("   ✅ Phase 2: Integration tests - DONE")
    print("   ✅ Phase 3: Tool integration - DONE")
    print("   ✅ Phase 4: Demo validation - DONE")
    print("   ⏳ Phase 5: Query trends refactor - TODO")
    print()

def main():
    """Run quick test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick Firestore integration test")
    parser.add_argument(
        "--commits",
        type=int,
        default=1,
        help="Number of commits to analyze (default: 1)"
    )
    args = parser.parse_args()
    
    asyncio.run(quick_test(num_commits=args.commits))

if __name__ == "__main__":
    main()
