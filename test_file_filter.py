"""Quick test to verify file filtering works."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.query_tools_v2 import filter_commits

# Test 1: Filter by app/main.py
print("=" * 80)
print("TEST 1: Filter commits touching app/main.py")
print("=" * 80)
result = filter_commits(
    repo="RostislavDublin/quality-guardian-test-fixture",
    files=["app/main.py"]
)
print(f"Status: {result['status']}")
print(f"Total found: {result.get('total_found', 0)}")
if result['status'] == 'success':
    print(f"Commits: {result['commits']}")
else:
    print(f"Message: {result.get('message', 'No message')}")

# Test 2: Filter with main.py (no app/ prefix)
print("\n" + "=" * 80)
print("TEST 2: Filter commits touching main.py (no prefix)")
print("=" * 80)
result2 = filter_commits(
    repo="RostislavDublin/quality-guardian-test-fixture",
    files=["main.py"]
)
print(f"Status: {result2['status']}")
print(f"Total found: {result2.get('total_found', 0)}")
if result2['status'] == 'success':
    print(f"Commits: {result2['commits'][:5]}...")  # First 5

# Test 3: Check what's actually in Firestore
print("\n" + "=" * 80)
print("TEST 3: What files are actually stored?")
print("=" * 80)
from storage.firestore_client import FirestoreAuditDB
db = FirestoreAuditDB()
commits = db.query_commits("RostislavDublin/quality-guardian-test-fixture", limit=3)
for c in commits[:3]:
    print(f"{c.commit_sha[:7]}: files_changed = {c.files_changed}")
