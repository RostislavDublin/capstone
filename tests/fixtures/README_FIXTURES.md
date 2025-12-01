# Test Fixtures - Deterministic Testing Infrastructure

## Overview

This directory provides **deterministic, reproducible test data** for Quality Guardian demos and tests.

## Structure

```
fixtures/
├── test-app/              # Clean template repository
│   ├── app/               # Application code
│   ├── tests/             # Test files
│   └── README.md
├── commits/               # Fixture commits with known diffs
│   ├── commit_01_add_logging.py
│   ├── commit_02_fix_sql_injection.py
│   ├── commit_03_add_password_validation.py
│   ├── commit_04_refactor_config.py
│   └── commit_05_add_validation.py
├── test_repo_fixture.py   # Repository management
└── test_fixture_commits.py # Fixture validation tests
```

## Usage

### Basic: All Commits at Once

```python
from fixtures.test_repo_fixture import reset_to_fixture_state

# Reset repository to clean state + all 5 commits
repo_name = reset_to_fixture_state(initial_commits=5)
# Now repository has all commits for testing
```

### Phased: Bootstrap + Sync Testing

```python
from fixtures.test_repo_fixture import (
    reset_to_fixture_state,
    apply_remaining_fixture_commits
)

# Phase 1: Bootstrap with 3 commits
repo_name = reset_to_fixture_state(initial_commits=3)
# Test bootstrap agent analyzing commits 1-3...

# Phase 2: Add 2 more commits for sync
added = apply_remaining_fixture_commits(start_from=4)  # Adds commits 4-5
# Test sync agent detecting 2 new commits...

# Test sync
# ...
```

## Fixture Commits

Each commit fixture contains:

- `COMMIT_MESSAGE`: Descriptive commit message
- `AUTHOR`, `AUTHOR_EMAIL`: Commit author
- `DIFF`: Full git unified diff
- `FILES_CHANGED`: List of modified files
- `ADDITIONS`, `DELETIONS`: Change statistics

### Commit 01: Add Logging
- Adds Python logging to `app/main.py`
- +6 lines, clean code

### Commit 02: Fix SQL Injection
- Fixes SQL injection vulnerability in `app/database.py`
- Security improvement: parameterized queries
- +2 -1 lines

### Commit 03: Add Password Validation
- Adds password strength validation to `app/utils.py`
- New function with regex checks
- +15 lines

### Commit 04: Refactor Config
- Simplifies configuration loading in `app/config.py`
- Code quality improvement
- +4 -11 lines

### Commit 05: Add Validation
- Integrates password validation into `app/main.py`
- New `register_user()` function
- +11 lines

## Key Functions

### `reset_to_fixture_state()`

Resets test repository (configured via `TEST_REPO_NAME` in `.env`) to clean, deterministic state:

1. Clones repository
2. Removes all existing files (except `.git`)
3. Copies clean `test-app` template
4. Applies 5 fixture commits with known diffs
5. Force pushes to GitHub

**Result**: Repository has exactly 6 commits:
- 1 clean template
- 5 fixture commits with predictable changes

### `add_test_commits(count)`

Adds N simple commits for sync testing. Each commit:
- Creates a timestamped file
- Has predictable message format
- Useful for testing "new commits" detection

## Testing Workflow

### Demo Setup (Every Run)

```python
# 1. Reset to fixture state
reset_to_fixture_state()
# Repository now has: template + 5 fixture commits

# 2. Clear RAG corpus
# (ensures no stale data)

# 3. Run demo
# Bootstrap: analyze 5 known commits
# Query: get predictable quality data
```

### Integration Tests

```python
# Test: Bootstrap
reset_to_fixture_state()
bootstrap_agent("repo", count=5)
# Verify: exactly 5 commits analyzed

# Test: Sync
add_test_commits(2)
sync_agent("repo")
# Verify: 2 new commits detected

# Test: Query
query_agent("show trends")
# Verify: data from 5 fixture commits
```

## Benefits

1. **Deterministic**: Same data every time
2. **Fast**: No manual setup needed
3. **Isolated**: Each test starts fresh
4. **Predictable**: Known commit SHAs, dates, quality scores
5. **Realistic**: Real code with real issues (SQL injection, complexity)

## Maintenance

To add new fixture commits:

1. Create `commit_06_*.py` in `commits/`
2. Define DIFF, metadata, expected changes
3. Update `_apply_fixture_commits()` in `test_repo_fixture.py`
4. Run validation: `python test_fixture_commits.py`

## Example: Full Demo Workflow

```bash
# 1. Clean setup
python demos/demo_quality_guardian_agent.py 1

# Behind the scenes:
# - reset_to_fixture_state() creates clean repo
# - Bootstrap analyzes 5 known commits
# - Query returns predictable trends
# - All timestamps, SHAs, scores are deterministic

# 2. Next run - same results
python demos/demo_quality_guardian_agent.py 1
# Identical output - same commits, same dates
```

## Why This Matters

Before fixtures:
- ❌ Tests relied on live GitHub repositories
- ❌ Data changed over time
- ❌ Flaky tests (commits added/removed)
- ❌ Hard to reproduce issues

After fixtures:
- ✅ Controlled test data
- ✅ Reproducible results
- ✅ Fast test execution
- ✅ Easy to debug

## Related Files

- `test-app/`: Clean application template
- `changesets.py`: Old PR-based fixtures (deprecated)
- `mock_pr.py`: Mock PR objects for unit tests
