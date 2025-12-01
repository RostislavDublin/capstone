"""Check why get_commit_details returns 12 instead of 13."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(Path(__file__).parent / "service-account-key.json")

from tools.query_tools_v2 import filter_commits, get_commit_details
from storage.firestore_client import FirestoreAuditDB

repo = "RostislavDublin/quality-guardian-test-fixture"
files = ["app/main.py"]

print("Step 1: filter_commits")
result1 = filter_commits(repo=repo, files=files)
print(f"Found {result1['total_found']} commits: {result1['commits']}")

print("\nStep 2: get_commit_details with scope='files'")
result2 = get_commit_details(
    repo=repo,
    commit_shas=result1['commits'],
    scope="files",
    files=files
)

print(f"Status: {result2['status']}")
print(f"Returned {len(result2.get('commits', []))} commits")

if result2['status'] == 'success':
    shas_returned = [c['sha'] for c in result2['commits']]
    print(f"SHAs returned: {shas_returned}")
    
    # Find missing SHA
    missing = set(result1['commits']) - set(shas_returned)
    if missing:
        print(f"\n❌ MISSING SHA: {missing}")
        
        # Step 3: Get details of missing commit from Firestore
        print("\n" + "="*80)
        print("Step 3: Inspecting missing commit")
        print("="*80)
        
        db = FirestoreAuditDB()
        all_commits = db.query_by_repository(repository=repo, limit=1000)
        
        for missing_sha in missing:
            for commit in all_commits:
                if commit.commit_sha.startswith(missing_sha):
                    print(f"\nCommit: {commit.commit_sha}")
                    print(f"Author: {commit.author}")
                    print(f"Date: {commit.date}")
                    print(f"Quality score: {commit.quality_score}")
                    print(f"files_changed: {commit.files_changed}")
                    print(f"Has file-level data: {hasattr(commit, 'files') and commit.files is not None}")
                    
                    if hasattr(commit, 'files') and commit.files:
                        print(f"Number of files in commit.files: {len(commit.files)}")
                        print("Files in commit.files:")
                        for f in commit.files:
                            print(f"  - {f.file_path}: quality={f.quality_score}")
                        
                        # Check if app/main.py is in files list
                        main_py_files = [f for f in commit.files if 'main.py' in f.file_path]
                        if main_py_files:
                            print(f"\n✅ app/main.py IS in commit.files: {[f.file_path for f in main_py_files]}")
                        else:
                            print(f"\n❌ app/main.py NOT in commit.files!")
                            print(f"   But it IS in files_changed: {'app/main.py' in commit.files_changed}")
                    else:
                        print("❌ No file-level data (commit.files is empty or None)")
                    break
    else:
        print("\n✅ All SHAs returned")
