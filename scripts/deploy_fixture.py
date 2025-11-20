#!/usr/bin/env python3
"""Deploy test fixture to GitHub as a new repository.

Creates RostislavDublin/code-review-test-fixture from template.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config


def run_command(cmd: list[str], cwd: str = None) -> tuple[bool, str]:
    """Run shell command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def deploy_fixture():
    """Deploy test fixture to GitHub."""
    print("🚀 Deploying test fixture to GitHub...\n")
    
    # Load config
    config = load_config()
    fixture_path = Path(__file__).parent.parent / config.test_fixture.local_path
    remote_repo = config.test_fixture.remote_repo
    
    if not fixture_path.exists():
        print(f"❌ Fixture path not found: {fixture_path}")
        return False
    
    print(f"📁 Fixture path: {fixture_path}")
    print(f"🎯 Target repo: {remote_repo}\n")
    
    # Check if already a git repo
    git_dir = fixture_path / ".git"
    if git_dir.exists():
        print("⚠️  Fixture is already a git repository")
        print("   Checking remote...")
        
        success, output = run_command(["git", "remote", "get-url", "origin"], cwd=str(fixture_path))
        if success:
            current_remote = output.strip()
            if remote_repo in current_remote:
                print(f"   ✅ Already connected to {remote_repo}")
                
                # Check for uncommitted changes
                success, output = run_command(["git", "status", "--porcelain"], cwd=str(fixture_path))
                if output.strip():
                    print("\n📝 Uncommitted changes detected. Committing...")
                    run_command(["git", "add", "-A"], cwd=str(fixture_path))
                    run_command(["git", "commit", "-m", "Update test fixture"], cwd=str(fixture_path))
                
                print("🔄 Pushing changes...")
                success, output = run_command(["git", "push"], cwd=str(fixture_path))
                if success:
                    print("   ✅ Pushed successfully")
                    return True
                else:
                    print(f"   ❌ Push failed: {output}")
                    return False
            else:
                print(f"   ⚠️  Connected to different repo: {current_remote}")
                print(f"   Expected: {remote_repo}")
                return False
    
    # Initialize new git repo
    print("📦 Initializing git repository...")
    success, _ = run_command(["git", "init"], cwd=str(fixture_path))
    if not success:
        print("   ❌ Failed to initialize git")
        return False
    print("   ✅ Initialized")
    
    # Create .gitignore if not exists
    gitignore_path = fixture_path / ".gitignore"
    if not gitignore_path.exists():
        print("   Creating .gitignore...")
        gitignore_path.write_text("""__pycache__/
*.py[cod]
.Python
env/
venv/
*.db
.vscode/
""")
    
    # Add and commit files
    print("📝 Committing files...")
    run_command(["git", "add", "-A"], cwd=str(fixture_path))
    success, _ = run_command(
        ["git", "commit", "-m", "Initial commit: Test fixture with documented issues"],
        cwd=str(fixture_path)
    )
    if not success:
        print("   ⚠️  Nothing to commit (already committed?)")
    else:
        print("   ✅ Committed")
    
    # Create GitHub repo using gh CLI
    print(f"\n🐙 Creating GitHub repository: {remote_repo}...")
    repo_name = remote_repo.split("/")[1]
    success, output = run_command([
        "gh", "repo", "create", repo_name,
        "--public",
        "--description", "Test fixture for AI Code Review system - contains intentionally bad code",
        "--source", str(fixture_path),
        "--push"
    ])
    
    if success:
        print(f"   ✅ Repository created: https://github.com/{remote_repo}")
    else:
        if "already exists" in output.lower():
            print(f"   ⚠️  Repository already exists")
            print("   Adding remote...")
            run_command(
                ["git", "remote", "add", "origin", f"https://github.com/{remote_repo}.git"],
                cwd=str(fixture_path)
            )
            print("   Pushing...")
            success, output = run_command(["git", "push", "-u", "origin", "main"], cwd=str(fixture_path))
            if not success:
                print(f"   ❌ Push failed: {output}")
                return False
        else:
            print(f"   ❌ Failed: {output}")
            return False
    
    print(f"\n✅ Test fixture deployed successfully!")
    print(f"   URL: https://github.com/{remote_repo}")
    print(f"\n💡 Next steps:")
    print(f"   1. Create test PRs: python scripts/create_test_prs.py")
    print(f"   2. Run evaluation: python scripts/verify_fixture.py")
    
    return True


if __name__ == "__main__":
    success = deploy_fixture()
    sys.exit(0 if success else 1)
