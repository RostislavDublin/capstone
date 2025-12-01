"""Fast GitHub API-based fixture reset (no git clone/push)."""

import os
import base64
import logging
from pathlib import Path
from datetime import datetime, timedelta
import importlib.util

from github import Github, InputGitTreeElement, InputGitAuthor
from dotenv import load_dotenv

# Load .env.dev if .env doesn't exist
if not load_dotenv():
    load_dotenv(".env.dev")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Get test repo from environment
TEST_REPO_NAME = os.getenv("TEST_REPO_NAME", "quality-guardian-test-fixture")
TEST_REPO_OWNER = os.getenv("TEST_REPO_OWNER", "RostislavDublin")
TEST_REPO_FULL = f"{TEST_REPO_OWNER}/{TEST_REPO_NAME}"
FIXTURE_PATH = Path(__file__).parent / "test-app"


def reset_to_fixture_state_api(initial_commits: int = 3) -> str:
    """Reset test repository using GitHub API (fast, no clone).
    
    Args:
        initial_commits: Number of fixture commits (1-15)
        
    Returns:
        Repository name
    """
    logger.info(f"\n🔄 Resetting {TEST_REPO_FULL} via GitHub API...\n")
    
    token = os.getenv("GITHUB_TOKEN")
    gh = Github(token)
    repo = gh.get_repo(TEST_REPO_FULL)
    
    # Get reference to main branch (we'll force update it)
    try:
        ref = repo.get_git_ref("heads/main")
        logger.info(f"📍 Will reset main branch (was: {ref.object.sha[:7]})")
    except Exception:
        ref = None
        logger.info("📍 No main branch, will create")
    
    # Step 1: Create tree with template files
    logger.info("📋 Creating template tree...")
    tree_elements = []
    
    def add_directory(dir_path: Path, prefix: str = ""):
        """Recursively add directory contents to tree."""
        for item in dir_path.iterdir():
            if item.name.startswith('.'):
                continue
                
            rel_path = prefix + item.name if prefix else item.name
            
            if item.is_file():
                with open(item, 'rb') as f:
                    content = f.read()
                blob = repo.create_git_blob(base64.b64encode(content).decode(), "base64")
                tree_elements.append(
                    InputGitTreeElement(
                        path=rel_path,
                        mode="100644",
                        type="blob",
                        sha=blob.sha
                    )
                )
            elif item.is_dir():
                add_directory(item, rel_path + "/")
    
    add_directory(FIXTURE_PATH)
    logger.info(f"  Added {len(tree_elements)} files")
    
    # Create base tree
    base_tree = repo.create_git_tree(tree_elements)
    
    # Create initial commit WITHOUT parents (fresh start)
    # Use historical date (35 days ago = before all fixture commits)
    logger.info("💾 Creating initial commit (fresh history)...")
    initial_date = datetime.now() - timedelta(days=35)
    initial_author = InputGitAuthor(
        name="Quality Guardian",
        email="bot@quality-guardian.dev",
        date=initial_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    commit = repo.create_git_commit(
        message="chore: Reset to test-app template",
        tree=base_tree,
        parents=[],  # No parents = new history
        author=initial_author,
        committer=initial_author
    )
    current_sha = commit.sha
    logger.info(f"  Commit: {current_sha[:7]} ({initial_date.strftime('%Y-%m-%d')})")
    
    # Step 2: Apply fixture commits
    logger.info(f"\n📦 Applying {initial_commits} fixture commits...")
    
    commits_dir = Path(__file__).parent / "commits"
    commit_files = [
        "commit_01_add_logging",
        "commit_02_fix_sql_injection",
        "commit_03_add_password_validation",
        "commit_04_refactor_config",
        "commit_05_add_validation",
        "commit_06_remove_validation",
        "commit_07_add_unsafe_feature",
        "commit_08_fix_upload_validation",
        "commit_09_restore_search_validation",
        "commit_10_add_caching",
        "commit_11_add_metrics",
        "commit_12_remove_eval",
        "commit_13_add_auth",
        "commit_14_rushed_feature",
        "commit_15_disable_logging",
    ][:initial_commits]
    
    # Start commits 30 days ago, then space 1 day apart
    base_date = datetime.now() - timedelta(days=30)
    
    for i, commit_name in enumerate(commit_files):
        commit_file = commits_dir / f"{commit_name}.py"
        
        # Import module
        spec = importlib.util.spec_from_file_location(commit_name, commit_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        logger.info(f"  {i+1}. {module.COMMIT_MESSAGE}")
        
        # Get parent commit/tree
        parent_commit = repo.get_git_commit(current_sha)
        
        # Create blobs for changed files
        tree_elements = []
        for file_path, content in module.FILES.items():
            blob = repo.create_git_blob(content, "utf-8")
            tree_elements.append(
                InputGitTreeElement(
                    path=file_path,
                    mode="100644",
                    type="blob",
                    sha=blob.sha
                )
            )
        
        # Create new tree (based on parent to keep other files)
        new_tree = repo.create_git_tree(tree_elements, base_tree=parent_commit.tree)
        
        # Create commit with historical date (1 day apart)
        commit_date = base_date + timedelta(days=i)
        author = InputGitAuthor(
            name=module.AUTHOR,
            email=module.AUTHOR_EMAIL,
            date=commit_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        commit = repo.create_git_commit(
            message=module.COMMIT_MESSAGE,
            tree=new_tree,
            parents=[parent_commit],
            author=author,
            committer=author
        )
        current_sha = commit.sha
        logger.info(f"     {current_sha[:7]}")
    
    # Step 3: Update main branch (force push new history)
    logger.info(f"\n🚀 Force updating main branch to {current_sha[:7]}...")
    
    if ref:
        ref.edit(current_sha, force=True)
    else:
        repo.create_git_ref("refs/heads/main", current_sha)
    
    logger.info("\n✅ Repository reset complete!\n")
    return TEST_REPO_FULL


if __name__ == "__main__":
    reset_to_fixture_state_api(initial_commits=3)
