#!/usr/bin/env python3
"""Generate valid git diff by applying code changes to a file.

This utility creates correct git diffs by:
1. Taking original file content
2. Applying specified modifications
3. Running real git diff to get proper hunk headers

Usage:
    python generate_demo_diff.py <base_file> <code_to_insert> [insert_after_pattern]
    
Or use programmatically:
    from scripts.generate_demo_diff import generate_diff
    diff = generate_diff(file_path, new_code, after="def some_function")
"""

import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional


def generate_diff(
    base_file: Path,
    code_to_insert: str,
    insert_after: Optional[str] = None,
    insert_before: Optional[str] = None,
    replace_pattern: Optional[str] = None,
    replacement: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> str:
    """Generate valid git diff by applying changes to a file.
    
    Args:
        base_file: Path to the file to modify
        code_to_insert: Code to insert (if inserting)
        insert_after: Pattern to find, insert code after this line
        insert_before: Pattern to find, insert code before this line
        replace_pattern: Pattern to find and replace (alternative to insert)
        replacement: Replacement text (used with replace_pattern)
        repo_root: Root directory of the repo (defaults to auto-detect via .git)
    
    Returns:
        Valid git diff string
    """
    if not base_file.exists():
        raise FileNotFoundError(f"Base file not found: {base_file}")
    
    # Determine relative path from repo root
    if repo_root is None:
        repo_root = base_file.parent
        while repo_root.parent != repo_root:
            if (repo_root / ".git").exists():
                break
            repo_root = repo_root.parent
    
    relative_path = base_file.relative_to(repo_root)
    
    # Create temp directory for git operations
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        temp_repo = temp_dir / "repo"
        
        # Copy entire repo to temp
        shutil.copytree(repo_root, temp_repo, ignore=shutil.ignore_patterns('.git'))
        
        # Initialize git
        subprocess.run(['git', 'init'], cwd=temp_repo, capture_output=True, check=True)
        subprocess.run(['git', 'add', '.'], cwd=temp_repo, capture_output=True, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=temp_repo, capture_output=True, check=True)
        
        # Modify file
        temp_file = temp_repo / relative_path
        lines = temp_file.read_text().split('\n')
        
        if replace_pattern and replacement:
            # Replace mode
            new_lines = []
            for line in lines:
                if replace_pattern in line:
                    new_lines.append(replacement)
                else:
                    new_lines.append(line)
            lines = new_lines
            
        elif insert_after:
            # Insert after pattern
            for i, line in enumerate(lines):
                if insert_after in line:
                    lines.insert(i + 1, code_to_insert)
                    break
            else:
                raise ValueError(f"Pattern not found: {insert_after}")
                
        elif insert_before:
            # Insert before pattern
            for i, line in enumerate(lines):
                if insert_before in line:
                    lines.insert(i, code_to_insert)
                    break
            else:
                raise ValueError(f"Pattern not found: {insert_before}")
        else:
            # Append at end
            lines.append(code_to_insert)
        
        temp_file.write_text('\n'.join(lines))
        
        # Generate diff
        result = subprocess.run(
            ['git', 'diff', str(relative_path)],
            cwd=temp_repo,
            capture_output=True,
            text=True,
            check=True
        )
        
        return result.stdout


def main():
    """CLI interface for generating diffs."""
    if len(sys.argv) < 3:
        print("Usage: generate_demo_diff.py <base_file> <code_to_insert> [insert_after_pattern]")
        print("\nExample:")
        print('  python generate_demo_diff.py app/db.py "def new_func():\\n    pass" "def old_func"')
        sys.exit(1)
    
    base_file = Path(sys.argv[1])
    code_to_insert = sys.argv[2]
    insert_after = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        diff = generate_diff(base_file, code_to_insert, insert_after=insert_after)
        print(diff)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
