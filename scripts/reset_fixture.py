#!/usr/bin/env python3
"""Reset fixture repository - delete and recreate from scratch."""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config


def main():
    """Reset fixture repository."""
    print("⚠️  RESET TEST FIXTURE")
    print("=" * 60)
    print("This will:")
    print("  1. Delete the remote GitHub repository")
    print("  2. Remove local .git directory")
    print("  3. Optionally re-deploy fresh")
    print()
    
    response = input("Are you sure? Type 'yes' to continue: ")
    if response.lower() != "yes":
        print("❌ Cancelled")
        return False
    
    config = load_config()
    fixture_path = Path(__file__).parent.parent / config.test_fixture.local_path
    remote_repo = config.test_fixture.remote_repo
    repo_name = remote_repo.split("/")[1]
    
    # Delete remote repo
    print(f"\n🗑️  Deleting remote repository: {remote_repo}...")
    try:
        subprocess.run(
            ["gh", "repo", "delete", remote_repo, "--yes"],
            check=True
        )
        print("   ✅ Deleted")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Failed (may not exist): {e}")
    
    # Remove local .git
    git_dir = fixture_path / ".git"
    if git_dir.exists():
        print(f"\n🗑️  Removing local .git directory...")
        import shutil
        shutil.rmtree(git_dir)
        print("   ✅ Removed")
    
    print("\n✅ Reset complete!")
    print(f"\n💡 To re-deploy:")
    print(f"   python scripts/deploy_fixture.py")
    print(f"   python scripts/create_test_prs.py")
    
    # Ask to redeploy
    redeploy = input("\nRe-deploy now? (y/n): ")
    if redeploy.lower() == "y":
        print("\n" + "="*60)
        from deploy_fixture import deploy_fixture
        if deploy_fixture():
            from create_test_prs import main as create_prs
            create_prs()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
