# Test Fixtures

This directory contains all test fixtures used by unit tests, integration tests, and demo scripts.

## Structure

```
tests/fixtures/
├── README.md              # This file
├── _generate_diffs.py     # Helper script to regenerate git diffs
├── changesets.py          # Python code samples for testing
├── mock_pr.py             # Mock Pull Request objects
├── test-app/              # Sample Flask application with intentional issues
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py    # Contains SQL injection vulnerabilities
│   │   ├── main.py
│   │   └── utils.py
│   ├── tests/
│   │   └── test_app.py
│   ├── README.md
│   └── requirements.txt
└── diffs/                 # Git diff fixtures
    ├── basic_pr.diff      # Simple PR with SQL injection
    └── complex_pr.diff    # Complex PR with SQL injection + high complexity
```

## test-app/

A minimal Flask application with intentional security and complexity issues for testing code review tools.

**Features:**
- 3 pre-existing SQL injection vulnerabilities in `app/database.py`
- Intentional code quality issues
- Valid Python syntax (can be executed)
- Used as base repository for testing merged-state analysis

**Usage in tests:**
```python
from pathlib import Path

test_app_path = Path(__file__).parent / "fixtures" / "test-app"
```

## diffs/

Pre-generated git diffs for testing diff parsing and analysis.

### basic_pr.diff

Simple pull request adding one function with SQL injection.

**Contains:**
- 1 new function: `execute_raw_query()`
- 1 SQL injection vulnerability
- ~8 lines of code

**Usage:**
```python
diff_path = Path(__file__).parent / "fixtures" / "diffs" / "basic_pr.diff"
diff_text = diff_path.read_text()
```

### complex_pr.diff

Complex pull request adding multiple functions with security and complexity issues.

**Contains:**
- 2 new functions: `execute_raw_query()`, `process_user_action()`
- 5 SQL injection vulnerabilities
- 1 high-complexity function (cyclomatic complexity >= 21, rank D)
- ~90 lines of code

**Used by:**
- `demos/demo_analyzer.py` - demonstrates Analyzer Agent capabilities

## changesets.py

Python code samples for testing changeset detection and categorization.

**Contains:**
- `SIMPLE_ADDITION` - basic function addition
- `REFACTORING` - code restructuring
- `BUG_FIX` - bug fix changeset
- `SECURITY_FIX` - security vulnerability fix
- `ALL_CHANGESETS` - complete list

**Usage:**
```python
from tests.fixtures.changesets import SIMPLE_ADDITION, ALL_CHANGESETS
```

## mock_pr.py

Mock GitHub Pull Request objects for testing without real API calls.

**Provides:**
- `create_mock_pr()` - creates mock PR with changeset
- `create_mock_pr_response()` - creates mock API response

**Usage:**
```python
from tests.fixtures.mock_pr import create_mock_pr

pr = create_mock_pr(SIMPLE_ADDITION)
```

## Regenerating Diffs

If you modify `test-app/app/database.py` or want to create new diffs, use `scripts/generate_demo_diff.py`:

```python
from pathlib import Path
from scripts.generate_demo_diff import generate_diff

test_app_root = Path("tests/fixtures/test-app")
base_file = test_app_root / "app" / "database.py"

code = '''
def my_function():
    pass
'''

diff = generate_diff(base_file, code, insert_after='# comment', repo_root=test_app_root)
Path("tests/fixtures/diffs/my_pr.diff").write_text(diff)
```

This ensures correct git diff format with proper hunk headers.

## Adding New Fixtures

### New Diff Fixtures

Use `scripts/generate_demo_diff.py` directly:

```python
from pathlib import Path
from scripts.generate_demo_diff import generate_diff

test_app_root = Path("tests/fixtures/test-app")
base_file = test_app_root / "app" / "database.py"

code = '''
def my_function():
    pass
'''

diff = generate_diff(
    base_file=base_file,
    code_to_insert=code,
    insert_after='# comment',  # or insert_before, replace_pattern
    repo_root=test_app_root
)

output = Path("tests/fixtures/diffs/my_pr.diff")
output.write_text(diff)
```

### New Code Samples

Add to `changesets.py`:

```python
NEW_CHANGESET = Changeset(
    description="Description",
    code="# code",
    category=ChangeCategory.FEATURE
)
```

## Notes

- All diffs use paths relative to `test-app/` root (e.g., `app/database.py`)
- Test-app is a valid Python project that can be executed
- Diffs are generated using real git to ensure correct hunk headers
- High complexity threshold: cyclomatic complexity >= 21 (rank D or higher)
