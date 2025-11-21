#!/usr/bin/env python3
"""
Quality Guardian Agent - Live Demonstration

This is an INTERACTIVE DEMO showing Quality Guardian in action:
- Analyzes a REAL GitHub repository
- Shows commit-by-commit analysis with file-level details  
- Demonstrates the full code quality workflow

NOT a test - this is a visual demonstration you can watch!
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import os
from dotenv import load_dotenv

from connectors.github import GitHubConnector
from audit.engine import AuditEngine

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env.dev")


def print_banner():
    """Print demo banner."""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║           🔧 BACKEND INTEGRATION TEST 🔧                          ║
║                                                                    ║
║  Testing: GitHubConnector + AuditEngine + FileAudit models       ║
║  NOT TESTED: ADK Agent, RAG Corpus, Orchestration layer          ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)


def print_section(title: str, emoji: str = "📋"):
    """Print section header."""
    print(f"\n{emoji} {title}")
    print("─" * 70)


def main():
    """Run the live demonstration."""
    print_banner()
    
    # STEP 1: Connect to GitHub
    print_section("STEP 1: Test GitHubConnector", "🔗")
    
    github_token = os.getenv("GITHUB_TOKEN", "")
    if not github_token or github_token == "your_github_token_here":
        print("❌ GITHUB_TOKEN not configured in .env.dev")
        print("   Please set your token in .env.dev")
        print("   Get token at: https://github.com/settings/tokens")
        return 1
    
    print(f"✅ GitHub token loaded: {'*' * 35}{github_token[-4:]}")
    
    try:
        connector = GitHubConnector(github_token)
        print("✅ Connector initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1
    
    # Target repository
    owner = "RostislavDublin"
    repo = "capstone"
    repo_identifier = f"{owner}/{repo}"
    print(f"🎯 Testing with: {repo_identifier}")
    
    # STEP 2: Get repository info
    print_section("STEP 2: Test GitHub API - Fetch Metadata", "📦")
    try:
        repo_info = connector.get_repository_info(repo_identifier)
        print(f"✅ Repository: {repo_info.name}")
        print(f"   Owner: {repo_info.owner}")
        print(f"   Default branch: {repo_info.default_branch}")
        print(f"   Primary language: {repo_info.language}")
        print(f"   Created: {repo_info.created_at.strftime('%Y-%m-%d')}")
        if repo_info.topics:
            print(f"   Topics: {', '.join(repo_info.topics[:5])}")
    except Exception as e:
        print(f"❌ Failed to get repository info: {e}")
        return 1
    
    # STEP 3: Fetch recent commits
    print_section("STEP 3: Fetch Recent Commits", "📝")
    try:
        print(f"⏳ Fetching commits from branch: {repo_info.default_branch}...")
        all_commits = connector.list_commits(
            repo_identifier,
            branch=repo_info.default_branch
        )
        if not all_commits:
            print("⚠️  No commits found in repository")
            return 1
        commits = all_commits[:3]  # Take first 3
        print(f"✅ Found {len(commits)} recent commits:\n")
        
        for i, commit in enumerate(commits, 1):
            print(f"   {i}. 🔖 {commit.sha[:8]}")
            print(f"      👤 {commit.author} <{commit.author_email}>")
            print(f"      📅 {commit.date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      💬 {commit.message[:70]}{'...' if len(commit.message) > 70 else ''}")
            print(f"      📊 +{commit.additions}/-{commit.deletions} lines")
            print()
            
    except Exception as e:
        print(f"❌ Failed to fetch commits: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # STEP 4: Initialize audit engine
    print_section("STEP 4: Initialize Quality Analysis Engine", "⚙️")
    try:
        audit_engine = AuditEngine(connector)
        print("✅ Audit engine initialized")
        print("   - Security scanner ready (bandit)")
        print("   - Complexity analyzer ready (radon)")
        print("   - Pattern matchers loaded")
    except Exception as e:
        print(f"❌ Failed to initialize audit engine: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # STEP 5: Analyze commits
    print_section("STEP 5: Test AuditEngine - Analyze Commits", "🔍")
    
    analyzed = 0
    for i, commit in enumerate(commits[:2], 1):  # Analyze first 2 commits
        print(f"\n{'='*70}")
        print(f"🔬 Analyzing Commit {i}/2: {commit.sha[:8]}")
        print(f"{'='*70}")
        print(f"📝 Message: {commit.message[:60]}{'...' if len(commit.message) > 60 else ''}")
        print(f"👤 Author: {commit.author}")
        print(f"📅 Date: {commit.date.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            # Audit the commit (AuditEngine will checkout the repo at this commit)
            print("\n⏳ Running AuditEngine.audit_commit()...")
            print("   (Creates temp checkout, runs bandit + radon)")
            audit = audit_engine.audit_commit(repo_identifier, commit)
            
            # Display results
            print("\n📊 RESULTS:")
            print(f"   Quality Score:    {audit.quality_score:.1f}/100")
            print(f"   Security Score:   {audit.security_score:.1f}/100")
            print(f"   Total Issues:     {audit.total_issues}")
            
            # Show issues breakdown
            has_issues = audit.total_issues > 0
            if has_issues:
                print(f"\n⚠️  ISSUES DETECTED ({audit.total_issues} total):")
                print(f"   🔴 Critical: {audit.critical_issues}")
                print(f"   🔴 High:     {audit.high_issues}")
                print(f"   🟡 Medium:   {audit.medium_issues}")
                print(f"   🔵 Low:      {audit.low_issues}")
                
                # Show security issues
                if audit.security_issues:
                    print("\n   Sample Security Issues:")
                    for issue in audit.security_issues[:2]:
                        print(f"      • [{issue['severity'].upper()}] {issue['message'][:70]}")
                        if 'file' in issue:
                            print(f"        File: {issue['file']}:{issue.get('line', '?')}")
                        
            else:
                print("\n✅ NO ISSUES DETECTED!")
                print("   This commit looks clean! 🎉")
            
            # Show file-level breakdown
            if audit.files:
                print(f"\n📁 FILE-LEVEL ANALYSIS ({len(audit.files)} files):")
                for j, file_audit in enumerate(audit.files[:5], 1):
                    issues_emoji = "⚠️" if file_audit.total_issues > 0 else "✅"
                    print(f"   {j}. {issues_emoji} {file_audit.file_path}")
                    print(f"      Quality Score: {file_audit.quality_score:.1f}/100")
                    if file_audit.total_issues > 0:
                        print(f"      Issues: {file_audit.total_issues} "
                              f"(High: {file_audit.high_issues}, Medium: {file_audit.medium_issues})")
                
                if len(audit.files) > 5:
                    print(f"   ... and {len(audit.files) - 5} more files")
            
            analyzed += 1
            
        except Exception as e:
            print(f"\n❌ Test failed for commit {commit.sha[:8]}: {e}")
            import traceback
            traceback.print_exc()
            # Exit on first error
            print("\n💥 Test stopped due to error.")
            return
    
    # SUMMARY - only shown if all commits analyzed successfully
    print_section("BACKEND INTEGRATION TEST COMPLETE", "✅")
    print(f"✅ Repository analyzed: {repo_identifier}")
    print(f"✅ Commits fetched: {len(commits)}")
    print(f"✅ Commits analyzed: {analyzed}")
    print()
    print("✅ Verified components:")
    print("  • GitHubConnector: API integration working")
    print("  • AuditEngine: Security + complexity analysis working")
    print("  • FileAudit models: Per-file tracking working")
    print()
    print("⏳ NOT IMPLEMENTED YET:")
    print("  • ADK Agent orchestration layer")
    print("  • RAG Corpus integration (persistent storage)")
    print("  • Multi-agent coordination")
    print("  • Command interface for end users")
    print()
    print("📍 Progress: ~15% of final system (backend tools only)")
    print()
    print("📍 Progress: ~15% of final system (backend tools only)")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
