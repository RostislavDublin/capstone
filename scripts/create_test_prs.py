#!/usr/bin/env python3
"""Create test PRs in fixture repository using changeset definitions."""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from changesets import ALL_CHANGESETS, Changeset


class TestPRCreator:
    """Creates test PRs from changeset definitions."""
    
    def __init__(self, fixture_path: Path, remote_repo: str):
        self.fixture_path = fixture_path
        self.remote_repo = remote_repo
    
    def run_git(self, args: List[str]) -> tuple[bool, str]:
        """Run git command in fixture directory."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.fixture_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
    
    def create_branch(self, branch_name: str) -> bool:
        """Create and checkout branch."""
        # Switch to main first
        self.run_git(["checkout", "main"])
        
        # Check if branch exists
        success, output = self.run_git(["branch", "--list", branch_name])
        if branch_name in output:
            print(f"   ⚠️  Branch {branch_name} already exists, using it")
            self.run_git(["checkout", branch_name])
            return True
        
        # Create new branch
        success, _ = self.run_git(["checkout", "-b", branch_name])
        return success
    
    def commit_and_push(self, message: str) -> bool:
        """Commit changes and push branch."""
        self.run_git(["add", "-A"])
        self.run_git(["commit", "-m", message])
        branch = self.run_git(["branch", "--show-current"])[1].strip()
        success, _ = self.run_git(["push", "-u", "origin", branch, "--force"])
        return success
    
    def create_pr(self, title: str, body: str, branch: str) -> bool:
        """Create PR using GitHub CLI."""
        try:
            subprocess.run(
                ["gh", "pr", "create",
                 "--repo", self.remote_repo,
                 "--title", title,
                 "--body", body,
                 "--base", "main",
                 "--head", branch],
                cwd=self.fixture_path,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def apply_changeset(self, changeset: Changeset) -> bool:
        """Apply a changeset to create a PR.
        
        Args:
            changeset: Changeset definition to apply
            
        Returns:
            True if PR created successfully
        """
        print(f"\n📋 Creating PR: {changeset.name} ({changeset.id})...")
        
        # Start from main
        self.run_git(["checkout", "main"])
        
        # Create branch
        if not self.create_branch(changeset.branch_name):
            return False
        
        # Apply changeset
        target_path = self.fixture_path / changeset.target_file
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        if changeset.operation == "add":
            # Add new file
            target_path.write_text(changeset.new_content)
            commit_msg = f"Add {changeset.target_file}"
            
        elif changeset.operation == "modify":
            # Modify existing file
            if changeset.new_content:
                # Replace entire file
                target_path.write_text(changeset.new_content)
            elif changeset.patch:
                # Apply patch (append to file)
                current = target_path.read_text() if target_path.exists() else ""
                target_path.write_text(current + "\n\n" + changeset.patch)
            commit_msg = f"Modify {changeset.target_file}"
            
        elif changeset.operation == "replace":
            # Replace file content
            target_path.write_text(changeset.new_content)
            commit_msg = f"Replace {changeset.target_file}"
        
        # Commit and push
        if not self.commit_and_push(commit_msg):
            return False
        
        # Build PR body from expected issues
        body_lines = [changeset.pr_body, "\n## Expected Issues (for testing)\n"]
        
        # Group by severity
        by_severity = {}
        for issue in changeset.expected_issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)
        
        severity_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "💡",
            "low": "ℹ️"
        }
        
        for severity in ["critical", "high", "medium", "low"]:
            if severity in by_severity:
                issues = by_severity[severity]
                body_lines.append(f"\n{severity_emoji[severity]} **{severity.upper()} ({len(issues)}):**")
                for issue in issues:
                    line_ref = f" (line {issue.line_start})" if issue.line_start else ""
                    must = " [MUST DETECT]" if issue.must_detect else ""
                    body_lines.append(f"- {issue.description}{line_ref}{must}")
        
        pr_body = "\n".join(body_lines)
        
        # Create PR
        return self.create_pr(changeset.pr_title, pr_body, changeset.branch_name)


def main():
    """Main entry point."""
    print("🎯 Creating test PRs from changeset definitions...\n")
    
    # Load config
    config = load_config()
    fixture_path = Path(__file__).parent.parent / config.test_fixture.local_path
    remote_repo = config.test_fixture.remote_repo
    
    if not fixture_path.exists():
        print(f"❌ Fixture not found: {fixture_path}")
        print("   Run deploy_fixture.py first")
        return False
    
    creator = TestPRCreator(fixture_path, remote_repo)
    
    # Create PRs from all changesets
    print(f"📦 Found {len(ALL_CHANGESETS)} changesets to deploy")
    
    results = []
    for changeset in ALL_CHANGESETS:
        success = creator.apply_changeset(changeset)
        results.append((changeset.name, success))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Summary:")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {name}")
    
    print(f"\n🔗 View PRs: https://github.com/{remote_repo}/pulls")
    print(f"📖 Changesets: {len(ALL_CHANGESETS)} defined in changesets.py")
    
    return all(success for _, success in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
