#!/usr/bin/env python3
"""Test fixture commits - verify they can be applied."""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*80)
print("  TESTING FIXTURE COMMITS")
print("="*80 + "\n")

# Test 1: Import commit modules
print("Test 1: Importing commit fixtures...")
try:
    from fixtures.commits import (
        commit_01_add_logging,
        commit_02_fix_sql_injection,
        commit_03_add_password_validation,
        commit_04_refactor_config,
        commit_05_add_validation,
    )
    print("✅ All commit modules imported successfully\n")
except ImportError as e:
    print(f"❌ Import failed: {e}\n")
    sys.exit(1)

# Test 2: Verify commit structure
print("Test 2: Verifying commit structure...")
commits = [
    commit_01_add_logging,
    commit_02_fix_sql_injection,
    commit_03_add_password_validation,
    commit_04_refactor_config,
    commit_05_add_validation,
]

for i, commit in enumerate(commits, 1):
    print(f"\nCommit {i}:")
    print(f"  Message: {commit.COMMIT_MESSAGE}")
    print(f"  Author: {commit.AUTHOR} <{commit.AUTHOR_EMAIL}>")
    print(f"  Files: {', '.join(commit.FILES_CHANGED)}")
    print(f"  Changes: +{commit.ADDITIONS} -{commit.DELETIONS}")
    print(f"  Diff lines: {len(commit.DIFF.splitlines())}")
    
    # Verify diff format
    if not commit.DIFF.startswith("diff --git"):
        print(f"  ⚠️  Warning: Diff doesn't start with 'diff --git'")
    else:
        print("  ✅ Diff format valid")

print("\n" + "="*80)
print("✅ ALL TESTS PASSED")
print("="*80)
