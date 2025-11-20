# Refactoring Plan - Holistic Review Architecture

**Date:** November 19, 2025  
**Context:** Shift from diff-only analysis to merged-state holistic review

> ⚠️ **TEMPORARY DOCUMENT** - Delete after refactoring complete  
> This is a working document for current implementation sprint only.

---

## Current Implementation Analysis

### What Works ✅

**1. diff_parser.py**
- `parse_git_diff()` - correctly extracts file changes, hunks, metadata
- `get_added_code_blocks()` - useful for extracting just new code
- Good test coverage (7/7 tests passing)

**2. security_scanner.py**
- `detect_security_issues()` - bandit integration works well
- Found 3 SQL injection issues when given full file
- Good test coverage (12/12 tests passing)

**3. complexity_analyzer.py**
- `calculate_complexity()` - radon integration works
- Correctly identifies high-complexity functions
- Good test coverage (13/13 tests passing)

**4. analyzer.py (AnalyzerAgent)**
- Multi-step pipeline is sound
- Gemini integration for AI recommendations works
- Clear progress logging

### What's Wrong ❌

**1. `get_modified_files_content()` in diff_parser.py**
```python
# CURRENT: Returns OLD version from base repo
if not patched_file.is_added_file:
    with open(original_path, 'r') as f:
        files_content[file_path] = f.read()  # ❌ OLD, not MERGED
```

**Problem:** We analyze the **before state**, not the **after merge** state!

**2. Analyzer Agent Input**
```python
# CURRENT: Takes diff_text + base_repo_path
def analyze_pull_request(self, diff_text: str, base_repo_path: str = None)
```

**Problem:** Should take **merged_repo_path** (result of applying PR), not base repo!

**3. Missing Repository Merger**
- No tool to apply PR and create merged state
- Manual workaround in demo (using old base files)

**4. Context Agent Not Started**
- No dependency graph analysis
- No integration point detection
- No affected modules identification

---

## Refactoring Plan

### Phase 1: Repository Merger Tool (HIGH PRIORITY)

**New File:** `src/tools/repo_merger.py`

```python
def create_merged_repository(
    base_repo_url: str,
    pr_diff: str,
    target_branch: str = "main"
) -> str:
    """Apply PR to base repository and return merged state.
    
    Steps:
    1. Create temp directory
    2. Clone base repo (or copy local)
    3. Apply PR patch via `git apply`
    4. Return path to merged state
    
    Returns:
        Absolute path to temporary merged repository
    """
    
def cleanup_merged_repository(merged_repo_path: str):
    """Remove temporary merged repository."""
```

**Tests needed:**
- Test applying simple PR (add file)
- Test applying modification PR
- Test applying multi-file PR
- Test cleanup

### Phase 2: Update Analyzer Agent (MEDIUM PRIORITY)

**Changes to `analyzer.py`:**

```python
# OLD signature
def analyze_pull_request(self, diff_text: str, base_repo_path: str = None)

# NEW signature  
def analyze_pull_request(
    self,
    merged_repo_path: str,
    changed_files: List[str],
    diff_metadata: dict = None  # Optional: for showing what changed
)
```

**New logic:**
1. Input: Path to merged repository (already applied PR)
2. Read complete files from merged repo (final state)
3. Run security/complexity on RESULT code
4. Use diff_metadata to highlight which parts are new (for reporting)

**Changes to `get_modified_files_content()`:**

```python
# RENAME to get_files_for_analysis()
def get_files_for_analysis(
    merged_repo_path: str,
    changed_file_paths: List[str]
) -> Dict[str, str]:
    """Read complete files from merged repository.
    
    Args:
        merged_repo_path: Path to repository AFTER PR merge
        changed_file_paths: List of files modified in PR
        
    Returns:
        Dict mapping file paths to complete file contents (merged state)
    """
    files = {}
    for file_path in changed_file_paths:
        full_path = Path(merged_repo_path) / file_path
        if full_path.exists():
            with open(full_path, 'r') as f:
                files[file_path] = f.read()
    return files
```

### Phase 3: Context Agent Implementation (HIGH PRIORITY)

**New File:** `src/agents/context.py`

**Responsibilities:**
1. Build dependency graph of merged repository
2. Find all modules that import changed files
3. Detect breaking changes (signature changes, removed functions)
4. Identify integration risks

**Tools needed:**
- `dependency_analyzer.py` - Python AST parsing to build import graph
- `integration_checker.py` - Compare old vs new API surface

**Example output:**
```python
{
    "affected_modules": ["app/views.py", "tests/test_database.py"],
    "breaking_changes": [
        {
            "file": "app/database.py",
            "function": "get_user_by_id",
            "issue": "Added required parameter 'include_deleted'",
            "callers": ["app/views.py:45", "app/admin.py:123"]
        }
    ],
    "integration_risks": [
        {
            "type": "new_dependency",
            "module": "sqlalchemy",
            "risk": "Not in requirements.txt"
        }
    ]
}
```

### Phase 4: Update Demo & Tests (MEDIUM PRIORITY)

**New demo flow:**
```python
# 1. Create merged repo
merged_path = create_merged_repository(
    base_repo_url="tests/fixtures/test-app",
    pr_diff=sample_diff
)

# 2. Get changed files from diff
changed_files = get_changed_files_from_diff(sample_diff)

# 3. Analyze merged state
agent = AnalyzerAgent()
result = agent.analyze_pull_request(
    merged_repo_path=merged_path,
    changed_files=changed_files
)

# 4. Cleanup
cleanup_merged_repository(merged_path)
```

**Update existing tests:**
- `test_diff_parser.py` - keep as-is (still useful)
- Add `test_repo_merger.py` - test merge logic
- Update `test_analyzer.py` - use merged repo fixtures

---

## Implementation Priority

### Week 1 (Now):
1. ✅ Update documentation (DONE)
2. ⏳ Build `repo_merger.py` tool
3. ⏳ Refactor `analyzer.py` to use merged repo
4. ⏳ Update demo to show correct workflow

### Week 2:
5. ⏳ Implement Context Agent basic version
6. ⏳ Add dependency graph analysis
7. ⏳ Integration tests for full workflow

---

## Migration Strategy

**Backward Compatibility:**
- Keep `get_added_code_blocks()` - still useful for getting just new code
- Keep existing tests - they validate low-level parsing
- Add new tests for merged-state workflow

**Incremental Rollout:**
1. Add repo merger tool (doesn't break existing code)
2. Add new methods alongside old ones
3. Update demo to use new workflow
4. Deprecate old methods after validation

---

## Success Criteria

✅ **Phase 1 Complete When:**
- Repo merger can apply real PR diffs
- Analyzer works on merged repository
- Demo shows SQL injection found in merged code
- All existing tests still pass

✅ **Phase 2 Complete When:**
- Context Agent detects affected modules
- Breaking changes identified automatically
- Integration risks reported in review

✅ **Full Migration Complete When:**
- System analyzes merged state, not diffs
- Holistic review covers integration points
- Competitive advantage vs simple linters proven

---

## Risk Assessment

**Low Risk:**
- Adding repo merger tool (new component)
- Updating docs (no code impact)

**Medium Risk:**
- Refactoring analyzer signature (breaks demo)
- Mitigation: Keep old method, deprecate gradually

**High Risk:**
- Context Agent complexity (dependency graph is hard)
- Mitigation: Start with simple import detection, iterate

---

**Next Steps:** Start with `repo_merger.py` implementation.
