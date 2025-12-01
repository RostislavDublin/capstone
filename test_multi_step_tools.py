"""Test multi-step tools for file-specific analysis.

This test verifies:
1. Agent uses filter_commits + get_commit_details for file queries
2. Returns file-specific quality scores (different from repo-level)
3. Performance: single DB query instead of multiple
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, 'src')
sys.path.insert(0, 'tests')

from agents.query_trends.agent import root_agent
from google.adk.runners import InMemoryRunner
from fixtures.test_repo_fixture import get_test_repo_name
from storage.firestore_client import FirestoreAuditDB

async def test():
    repo = get_test_repo_name()
    runner = InMemoryRunner(agent=root_agent, app_name='agents')
    
    # Get actual commit dates
    db = FirestoreAuditDB()
    commits = db.query_by_repository(repository=repo, limit=20, descending=False)
    
    if not commits or len(commits) < 5:
        print("ERROR: Not enough commits. Run demo_quality_guardian_agent.py first.")
        return
    
    print(f"\n{'='*80}")
    print(f"  TEST: Multi-Step Tools for File-Specific Analysis")
    print(f"{'='*80}\n")
    
    print(f"Repository: {repo}")
    print(f"Total commits: {len(commits)}")
    print(f"Date range: {commits[0].date.strftime('%Y-%m-%d')} to {commits[-1].date.strftime('%Y-%m-%d')}\n")
    
    # Test 1: Repository-level (uses query_trends)
    print("="*80)
    print("TEST 1: Repository-level query (all files)")
    print("="*80 + "\n")
    
    query1 = f"Show quality trends for {repo}"
    print(f"Query: {query1}\n")
    
    import io, contextlib
    f1 = io.StringIO()
    with contextlib.redirect_stdout(f1):
        await runner.run_debug(query1)
    
    output1 = f1.getvalue()
    
    # Check which tools were used
    if 'query_trends' in output1 and 'filter_commits' not in output1:
        print("✅ PASS: Used query_trends (correct for repo-level)\n")
    else:
        print("❌ FAIL: Did not use query_trends\n")
    
    # Extract repo-level score
    repo_score = None
    for line in output1.split('\n'):
        if 'Start:' in line and '/100' in line:
            try:
                repo_score = float(line.split('Start:')[1].split('/100')[0].strip())
                print(f"Repository-level score: {repo_score}/100\n")
                break
            except:
                pass
    
    # Test 2: File-specific (uses filter_commits + get_commit_details)
    print("="*80)
    print("TEST 2: File-specific query (app/main.py only)")
    print("="*80 + "\n")
    
    query2 = f"Show quality trends for app/main.py in {repo}"
    print(f"Query: {query2}\n")
    
    f2 = io.StringIO()
    with contextlib.redirect_stdout(f2):
        await runner.run_debug(query2)
    
    output2 = f2.getvalue()
    
    # Check which tools were used
    tools_correct = False
    if 'filter_commits: Found' in output2:
        print("✅ Step 1: filter_commits called")
        if 'get_commit_details: Retrieved' in output2 and 'scope=files' in output2:
            print("✅ Step 2: get_commit_details(scope='files') called")
            tools_correct = True
        else:
            print("❌ Step 2: get_commit_details NOT called correctly")
    else:
        print("❌ Step 1: filter_commits NOT called")
    
    # Check DB query count
    db_queries = output2.count('Retrieved 16 commits')
    print(f"✅ Database queries: {db_queries} (should be 1, not 12)")
    
    # Extract file-level score
    file_score = None
    for line in output2.split('\n'):
        if 'Start:' in line and '/100' in line:
            try:
                file_score = float(line.split('Start:')[1].split('/100')[0].strip())
                print(f"\nFile-specific score: {file_score}/100")
                break
            except:
                pass
    
    # Test 3: Comparison
    print("\n" + "="*80)
    print("RESULT: Score Comparison")
    print("="*80 + "\n")
    
    if repo_score is not None and file_score is not None:
        print(f"Repository-level (all files):  {repo_score}/100")
        print(f"File-specific (app/main.py):   {file_score}/100")
        print(f"Difference:                     {abs(repo_score - file_score):.1f} points")
        
        if repo_score != file_score:
            print("\n✅ PASS: Scores are different (file-specific works!)")
        else:
            print("\n⚠️  WARNING: Scores are identical (may indicate issue)")
    else:
        print("❌ FAIL: Could not extract scores")
    
    # Final verdict
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80 + "\n")
    
    if tools_correct and db_queries == 1:
        print("✅ ALL TESTS PASSED")
        print("   - Multi-step workflow works correctly")
        print("   - Performance optimized (1 DB query)")
        print("   - File-specific analysis functional")
    else:
        print("❌ SOME TESTS FAILED")
        if not tools_correct:
            print("   - Multi-step workflow not working")
        if db_queries != 1:
            print(f"   - Too many DB queries ({db_queries} instead of 1)")
    
    print()

if __name__ == "__main__":
    asyncio.run(test())
