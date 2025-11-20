"""Repository merger tool for applying PR diffs to create merged state.

This tool creates a temporary repository with PR changes applied,
enabling analysis of the complete merged state rather than just diff chunks.
"""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional


def create_merged_repository(
    base_repo_path: str,
    pr_diff: str,
    cleanup_on_error: bool = True
) -> str:
    """Apply PR diff to base repository and return merged state path.
    
    Creates a temporary copy of the base repository and applies the PR patch,
    returning the path to the merged state for analysis.
    
    Args:
        base_repo_path: Path to base repository (local path)
        pr_diff: Git unified diff string to apply
        cleanup_on_error: Whether to cleanup temp directory on error (default: True)
        
    Returns:
        Absolute path to temporary merged repository
        
    Raises:
        ValueError: If base_repo_path doesn't exist or is not a directory
        RuntimeError: If git apply fails
        
    Example:
        >>> merged_path = create_merged_repository(
        ...     "tests/fixtures/test-app",
        ...     diff_content
        ... )
        >>> # Analyze merged_path...
        >>> cleanup_merged_repository(merged_path)
    """
    base_path = Path(base_repo_path).resolve()
    
    # Validate base repository
    if not base_path.exists():
        raise ValueError(f"Base repository not found: {base_repo_path}")
    if not base_path.is_dir():
        raise ValueError(f"Base repository is not a directory: {base_repo_path}")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="pr_review_")
    temp_path = Path(temp_dir)
    
    try:
        # Copy base repository to temp location
        merged_path = temp_path / "repo"
        shutil.copytree(base_path, merged_path, symlinks=True)
        
        # Write diff to temporary file
        diff_file = temp_path / "pr.patch"
        with open(diff_file, 'w', encoding='utf-8') as f:
            f.write(pr_diff)
        
        # Apply patch using git apply
        result = subprocess.run(
            ['git', 'apply', '--whitespace=nowarn', str(diff_file)],
            cwd=merged_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"Failed to apply patch: {result.stderr}"
            if cleanup_on_error:
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(error_msg)
        
        # Remove patch file (not needed anymore)
        diff_file.unlink()
        
        return str(merged_path)
        
    except Exception:
        if cleanup_on_error:
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def cleanup_merged_repository(merged_repo_path: str):
    """Remove temporary merged repository.
    
    Cleans up the temporary directory created by create_merged_repository.
    Safe to call multiple times or with non-existent paths.
    
    Args:
        merged_repo_path: Path to merged repository (from create_merged_repository)
        
    Example:
        >>> merged_path = create_merged_repository(...)
        >>> try:
        ...     # Do analysis
        ...     pass
        ... finally:
        ...     cleanup_merged_repository(merged_path)
    """
    if not merged_repo_path:
        return
    
    merged_path = Path(merged_repo_path)
    
    # Only cleanup if it's in a temp directory (safety check)
    if not str(merged_path).startswith(tempfile.gettempdir()):
        # Not a temp directory, don't delete
        return
    
    # Remove the parent temp directory (contains both repo and patch file)
    temp_dir = merged_path.parent
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


def get_changed_files_from_diff(pr_diff: str) -> list[str]:
    """Extract list of changed file paths from diff.
    
    Parses a git unified diff and returns the list of files that were
    added, modified, or deleted.
    
    Args:
        pr_diff: Git unified diff string
        
    Returns:
        List of file paths (relative to repository root)
        
    Example:
        >>> diff = "diff --git a/app/main.py b/app/main.py\\n..."
        >>> get_changed_files_from_diff(diff)
        ['app/main.py']
    """
    from tools.diff_parser import parse_git_diff
    
    diff_analysis = parse_git_diff(pr_diff)
    return [fc.path for fc in diff_analysis.files_changed]
