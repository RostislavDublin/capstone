#!/usr/bin/env python3
"""Quick test: Verify Firestore integration with repository tools.

Tests analyze_repository and list_analyzed_repositories with real Firestore.
Uses test fixture repo (fast, no external API calls for commits).
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

def test_integration():
    """Test Firestore integration end-to-end."""
    print("=" * 60)
    print("PHASE 4: Testing Firestore Integration")
    print("=" * 60)
    
    # Import after path setup
    from tools.repository_tools import analyze_repository, list_analyzed_repositories
    from storage.firestore_client import FirestoreAuditDB
    
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    test_repo = "RostislavDublin/quality-guardian-test-fixture"
    
    print(f"\nProject: {project}")
    print(f"Test repo: {test_repo}")
    
    # Initialize Firestore client
    db = FirestoreAuditDB(
        project_id=project,
        database="(default)",
        collection_prefix="quality-guardian"
    )
    
    # Clean up test data if exists
    print(f"\n1️⃣  Cleaning up old test data...")
    repos_before = db.get_repositories()
    if test_repo in repos_before:
        db.delete_repository(test_repo)
        print(f"   ✓ Deleted old data for {test_repo}")
    else:
        print(f"   ✓ No old data found")
    
    # Test analyze_repository (dual write to Firestore + RAG)
    print(f"\n2️⃣  Testing analyze_repository (1 commit)...")
    result = analyze_repository(repo=test_repo, count=1)
    
    if result.get("status") == "success":
        print(f"   ✓ Analysis successful")
        print(f"   - Commits analyzed: {result['commits_analyzed']}")
        print(f"   - Avg quality: {result['avg_quality_score']}")
        print(f"   - Total issues: {result['total_issues']}")
    else:
        print(f"   ✗ Analysis failed: {result.get('error', 'Unknown error')}")
        return False
    
    # Verify Firestore write
    print(f"\n3️⃣  Verifying Firestore write...")
    repos_after = db.get_repositories()
    
    if test_repo in repos_after:
        print(f"   ✓ Repository found in Firestore")
        
        stats = db.get_repository_stats(test_repo)
        print(f"   - Total commits: {stats['total_commits']}")
        print(f"   - Last analyzed: {stats['last_analyzed']}")
        
        commits = db.query_by_repository(test_repo, limit=10)
        print(f"   - Commits in DB: {len(commits)}")
        
        if len(commits) > 0:
            print(f"   ✓ Commit data stored successfully")
            print(f"   - First commit SHA: {commits[0].commit_sha[:7]}")
        else:
            print(f"   ✗ No commits found in Firestore")
            return False
    else:
        print(f"   ✗ Repository NOT found in Firestore")
        return False
    
    # Test list_analyzed_repositories
    print(f"\n4️⃣  Testing list_analyzed_repositories...")
    list_result = list_analyzed_repositories()
    
    if list_result.get("status") == "success":
        repos = list_result["repositories"]
        print(f"   ✓ List successful")
        print(f"   - Total repositories: {list_result['total_repositories']}")
        print(f"   - Total commits: {list_result['total_commits']}")
        
        # Find our test repo
        test_repo_found = False
        for repo_info in repos:
            if repo_info["repository"] == test_repo:
                test_repo_found = True
                print(f"   ✓ Test repo found in list")
                print(f"   - Commits: {repo_info['total_commits']}")
                print(f"   - Last analyzed: {repo_info['last_analyzed']}")
                break
        
        if not test_repo_found:
            print(f"   ✗ Test repo NOT in list")
            return False
    else:
        print(f"   ✗ List failed: {list_result.get('error', 'Unknown error')}")
        return False
    
    # Cleanup
    print(f"\n5️⃣  Cleaning up test data...")
    db.delete_repository(test_repo)
    print(f"   ✓ Test data deleted")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Firestore integration working!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
