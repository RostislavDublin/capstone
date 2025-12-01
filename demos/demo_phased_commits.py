#!/usr/bin/env python3
"""Demo: Phased commit application (bootstrap + sync).

Shows how to:
1. Reset repo with 3 commits (bootstrap phase)
2. Add 2 more commits (sync phase)
"""

import sys
from pathlib import Path

# Add src and tests to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "tests"))

from fixtures.fast_reset_api import reset_to_fixture_state_api
from fixtures import apply_remaining_fixture_commits
from fixtures.test_repo_fixture import get_test_repo_name
from github import Github
import os
from dotenv import load_dotenv

load_dotenv(project_root / ".env")

TEST_REPO_FULL = get_test_repo_name()


def main():
    """Demonstrate phased commit application."""
    print("\n" + "=" * 80)
    print("DEMO: Phased Commit Application")
    print("=" * 80 + "\n")
    
    # Phase 1: Bootstrap with 3 commits
    print("📦 PHASE 1: Bootstrap (3 commits)")
    print("-" * 80)
    last_sha = reset_to_fixture_state_api(initial_commits=3)
    print(f"Reset complete: {last_sha}")
    
    # Verify we have 3 commits
    github_token = os.getenv("GITHUB_TOKEN")
    gh = Github(github_token)
    repo = gh.get_repo(TEST_REPO_FULL)
    commits_list = list(repo.get_commits())
    print(f"\n✅ Repository has {len(commits_list)} commits:")
    for i, commit in enumerate(commits_list, 1):
        print(f"  {i}. {commit.commit.message.splitlines()[0]}")
    
    print("\n" + "=" * 80)
    input("\n⏸️  Press Enter to add more commits for sync phase...")
    print()
    
    # Phase 2: Add remaining commits
    print("📦 PHASE 2: Sync (adding 2 more commits)")
    print("-" * 80)
    added = apply_remaining_fixture_commits(start_from=4)
    print(f"Added {added} commits")
    
    # Verify we now have 5 commits
    commits_list = list(repo.get_commits())
    print(f"\n✅ Repository now has {len(commits_list)} commits:")
    for i, commit in enumerate(commits_list, 1):
        print(f"  {i}. {commit.commit.message.splitlines()[0]}")
    
    print("\n" + "=" * 80)
    print("✅ Demo complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
