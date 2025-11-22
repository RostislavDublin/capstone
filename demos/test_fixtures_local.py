#!/usr/bin/env python3
"""Quick test: Apply fixture commits locally without GitHub."""

import sys
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from fixtures.test_repo_fixture import _apply_fixture_commits

def main():
    """Test fixture application locally."""
    print("Testing fixture commits locally (no GitHub)...\n")
    
    # Create temp repo
    temp_dir = Path("/tmp/test-fixtures-local")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)
    
    # Init git
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=temp_dir,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_dir,
        check=True,
        capture_output=True
    )
    
    # Copy template
    template = Path(__file__).parent.parent / "tests/fixtures/test-app"
    for item in template.iterdir():
        if item.name == ".git":
            continue
        dest = temp_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    
    # Commit template
    subprocess.run(["git", "add", "-A"], cwd=temp_dir, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=temp_dir,
        check=True,
        capture_output=True
    )
    
    print("Applying 3 fixture commits...")
    _apply_fixture_commits(temp_dir, start=0, count=3)
    
    # Show result
    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=temp_dir,
        capture_output=True,
        text=True
    )
    print("\nCommits created:")
    print(result.stdout)
    
    # Show last commit files
    result = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:"],
        cwd=temp_dir,
        capture_output=True,
        text=True
    )
    print("\nFiles changed in last commit:")
    print(result.stdout)
    
    print(f"\nTest repo: {temp_dir}")
    print("SUCCESS!")

if __name__ == "__main__":
    main()
