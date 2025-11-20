"""Git diff parsing tool for code analysis.

Uses unidiff library to parse unified diffs and extract structured information
about file changes, additions, deletions, and context.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from unidiff import PatchSet


@dataclass
class FileChange:
    """Represents changes to a single file."""
    path: str
    old_path: Optional[str]
    is_new_file: bool
    is_deleted_file: bool
    is_renamed: bool
    added_lines: int
    removed_lines: int
    hunks: List[Dict[str, Any]]


@dataclass 
class DiffAnalysis:
    """Structured analysis of a git diff."""
    files_changed: List[FileChange]
    total_additions: int
    total_deletions: int
    modified_files: int
    new_files: int
    deleted_files: int


def parse_git_diff(diff_text: str) -> DiffAnalysis:
    """Parse unified git diff into structured format.
    
    This is a TOOL function that can be used by ADK agents.
    Extracts file changes, line modifications, and change statistics.
    
    Args:
        diff_text: Unified diff format string (output of git diff)
        
    Returns:
        DiffAnalysis with structured information about all changes
        
    Raises:
        ValueError: If diff_text is empty or invalid format
    """
    if not diff_text or not diff_text.strip():
        raise ValueError("diff_text cannot be empty")
    
    try:
        patch_set = PatchSet(diff_text)
    except Exception as e:
        raise ValueError(f"Invalid diff format: {e}")
    
    files_changed = []
    total_additions = 0
    total_deletions = 0
    new_files = 0
    deleted_files = 0
    
    for patched_file in patch_set:
        # Extract file metadata
        is_new = patched_file.is_added_file
        is_deleted = patched_file.is_removed_file
        is_renamed = patched_file.is_rename
        
        if is_new:
            new_files += 1
        if is_deleted:
            deleted_files += 1
        
        # Count line changes
        added = sum(1 for hunk in patched_file for line in hunk if line.is_added)
        removed = sum(1 for hunk in patched_file for line in hunk if line.is_removed)
        
        total_additions += added
        total_deletions += removed
        
        # Extract hunks with context
        hunks = []
        for hunk in patched_file:
            hunk_data = {
                'source_start': hunk.source_start,
                'source_length': hunk.source_length,
                'target_start': hunk.target_start,
                'target_length': hunk.target_length,
                'section_header': hunk.section_header,
                'added_lines': [],
                'removed_lines': [],
                'context_lines': []
            }
            
            for line in hunk:
                line_data = {
                    'line_number': line.target_line_no if line.is_added else line.source_line_no,
                    'content': line.value.rstrip('\n')
                }
                
                if line.is_added:
                    hunk_data['added_lines'].append(line_data)
                elif line.is_removed:
                    hunk_data['removed_lines'].append(line_data)
                else:
                    hunk_data['context_lines'].append(line_data)
            
            hunks.append(hunk_data)
        
        file_change = FileChange(
            path=patched_file.path,
            old_path=patched_file.source_file if is_renamed else None,
            is_new_file=is_new,
            is_deleted_file=is_deleted,
            is_renamed=is_renamed,
            added_lines=added,
            removed_lines=removed,
            hunks=hunks
        )
        files_changed.append(file_change)
    
    return DiffAnalysis(
        files_changed=files_changed,
        total_additions=total_additions,
        total_deletions=total_deletions,
        modified_files=len(patch_set),
        new_files=new_files,
        deleted_files=deleted_files
    )


def get_added_code_blocks(diff_analysis: DiffAnalysis) -> Dict[str, List[str]]:
    """Extract all added code blocks by file.
    
    Useful for security scanning and complexity analysis of new code.
    
    Args:
        diff_analysis: Parsed diff analysis
        
    Returns:
        Dict mapping file paths to list of added code snippets
    """
    code_blocks = {}
    
    for file_change in diff_analysis.files_changed:
        if file_change.is_deleted_file:
            continue
            
        added_lines = []
        for hunk in file_change.hunks:
            for line in hunk['added_lines']:
                added_lines.append(line['content'])
        
        if added_lines:
            code_blocks[file_change.path] = added_lines
    
    return code_blocks


def get_modified_files_content(
    diff_text: str,
    base_repo_path: str
) -> Dict[str, str]:
    """Get full file contents for analysis.
    
    For new files: extracts complete content from diff
    For modified files: reads the ENTIRE original file from base repo
    
    This ensures security/complexity scanners have full file context.
    Note: This analyzes the OLD version, not the patched version.
    For code review, we care about what's ALREADY in the repo.
    
    Args:
        diff_text: Git diff in unified format
        base_repo_path: Path to base repository
        
    Returns:
        Dict mapping file paths to complete file contents
    """
    from pathlib import Path
    
    patch_set = PatchSet(diff_text)
    files_content = {}
    
    for patched_file in patch_set:
        if patched_file.is_removed_file:
            continue
            
        file_path = patched_file.path
        
        if patched_file.is_added_file:
            # New file: extract all added lines
            lines = []
            for hunk in patched_file:
                for line in hunk:
                    if line.is_added:
                        lines.append(line.value.rstrip('\n\r'))
            files_content[file_path] = '\n'.join(lines)
        else:
            # Modified file: read original file completely
            original_path = Path(base_repo_path) / file_path
            if original_path.exists():
                with open(original_path, 'r', encoding='utf-8') as f:
                    files_content[file_path] = f.read()
            else:
                # Fallback: extract added lines if original not found
                lines = []
                for hunk in patched_file:
                    for line in hunk:
                        if line.is_added:
                            lines.append(line.value.rstrip('\n\r'))
                if lines:
                    files_content[file_path] = '\n'.join(lines)
    
    return files_content

