# Unified Changeset Testing Architecture

**Status:** ✅ Implemented (Day 2, Nov 19 2025)

## Overview

Complete testing infrastructure with **single source of truth** for all test scenarios.

## The Problem It Solves

**Before:** Test definitions scattered across multiple places
- ❌ evalset.json has expected outcomes
- ❌ scripts/create_test_prs.py has hardcoded test code
- ❌ Local tests use different test data
- ❌ Updating tests requires changes in 3+ places

**After:** Unified changeset definitions
- ✅ `changesets.py` defines ALL test scenarios once
- ✅ Used for local unit/integration tests
- ✅ Used for remote E2E tests
- ✅ Used for sequential learning evaluation
- ✅ Single update propagates everywhere

## Architecture

```
changesets.py                           # SOURCE OF TRUTH
    ├── Changeset definitions
    │   ├── Code content (new_content/patch)
    │   ├── Expected issues (type, severity, location)
    │   ├── PR metadata (title, body, branch)
    │   └── Test criteria (min issues, max FP, time)
    │
    ├─→ Local Testing (Fast)
    │   ├── tools/diff_generator.py → synthetic diffs
    │   ├── tools/mock_pr_context.py → PullRequest objects
    │   └── tests/test_changesets.py → unit tests
    │
    ├─→ Remote E2E Testing (Real GitHub)
    │   ├── scripts/deploy_fixture.py → creates repo
    │   ├── scripts/create_test_prs.py → applies changesets as PRs
    │   ├── evalsets/test_fixture_prs.evalset.json → references changesets
    │   └── adk eval → tests on real PRs
    │
    └─→ Sequential Learning (Memory Bank)
        ├── tests/learning/sequential_runner.py
        └── Demonstrates improvement over time
```

## Key Files

### 1. changesets.py (426 lines)
**Purpose:** Single source of truth for all test scenarios

**Contains:**
- `Changeset` Pydantic model
- `ExpectedIssue` Pydantic model
- 4 changeset definitions (CHANGESET_01 through CHANGESET_04)
- Registry: `ALL_CHANGESETS`, `CHANGESETS_BY_ID`, `CHANGESETS_BY_CATEGORY`
- Helper functions: `get_changeset()`, `get_changesets_by_category()`

**Example:**
```python
CHANGESET_01_SQL_INJECTION = Changeset(
    id="cs-01-sql-injection",
    operation="add",
    target_file="app/auth.py",
    new_content="""...SQL injection code...""",
    expected_issues=[
        ExpectedIssue(
            type="sql_injection",
            severity="critical",
            must_detect=True,
            ...
        )
    ],
    pr_title="Add user authentication",
    pr_body="...",
    branch_name="feature/user-authentication",
    min_issues_to_detect=2,
    max_false_positives=0,
    target_processing_time=30.0
)
```

### 2. tools/diff_generator.py
**Purpose:** Generate synthetic git diffs from changesets

**Functions:**
- `generate_diff()` - Create git diff format
- `generate_diff_from_changeset()` - From Changeset object
- `generate_all_diffs()` - Batch generate all diffs

**Usage:**
```python
from capstone.changesets import CHANGESET_01_SQL_INJECTION
from capstone.tools.diff_generator import generate_diff_from_changeset

diff = generate_diff_from_changeset(CHANGESET_01_SQL_INJECTION)
# Returns git diff format string
```

### 3. tools/mock_pr_context.py
**Purpose:** Create PullRequest objects from changesets

**Functions:**
- `create_mock_pr_from_changeset()` - Full PullRequest object
- `create_all_mock_prs()` - Batch create all PRs
- `create_mock_pr_context_dict()` - Simple dict version

**Usage:**
```python
from capstone.tools.mock_pr_context import create_mock_pr_from_changeset

pr = create_mock_pr_from_changeset(CHANGESET_01_SQL_INJECTION)
# Returns PullRequest with author, metadata, diff, files
```

### 4. scripts/create_test_prs.py
**Purpose:** Apply changesets to GitHub as real PRs

**Key Method:**
```python
def apply_changeset(self, changeset: Changeset) -> bool:
    """Apply changeset: create branch, commit changes, push, create PR."""
```

**Workflow:**
1. Reads `ALL_CHANGESETS` from `changesets.py`
2. For each changeset:
   - Creates branch (from changeset.branch_name)
   - Applies file changes (add/modify/replace)
   - Commits with descriptive message
   - Pushes branch
   - Creates PR with formatted body from expected_issues
3. PRs use metadata from changeset definitions

### 5. evalsets/test_fixture_prs.evalset.json
**Purpose:** ADK evaluation dataset referencing changesets

**Structure:**
```json
{
  "id": "security-01",
  "changeset_id": "cs-01-sql-injection",
  "name": "SQL Injection Detection",
  "description": "..."
}
```

**Links test cases to changeset definitions** via `changeset_id` field.

### 6. tests/test_changesets.py
**Purpose:** Comprehensive unit tests for infrastructure

**Test Classes:**
- `TestChangesetInfrastructure` - Validate changeset definitions
- `TestDiffGeneration` - Test synthetic diff creation
- `TestMockPRCreation` - Test PullRequest object creation
- `TestChangesetLookup` - Test helper functions
- `TestChangesetExpectations` - Validate expected issues
- `TestAgentWithChangesets` - Example agent tests (skipped)

### 7. docs/testing-strategy.md
**Purpose:** Complete documentation of testing approach

**Sections:**
- Architecture overview
- Local testing (unit/integration)
- Remote E2E testing
- Sequential learning tests
- Test fixture management
- Running tests
- Adding new test cases

## Workflow Examples

### Local Unit Test
```python
# 1. Get changeset
from capstone.changesets import CHANGESET_01_SQL_INJECTION

# 2. Generate diff
from capstone.tools.diff_generator import generate_diff_from_changeset
diff = generate_diff_from_changeset(CHANGESET_01_SQL_INJECTION)

# 3. Test agent
result = await analyzer_agent.analyze_diff(diff)

# 4. Verify against changeset expectations
critical = [i for i in result.issues if i.severity == "critical"]
expected = [i for i in CHANGESET_01_SQL_INJECTION.expected_issues 
            if i.severity == "critical"]
assert len(critical) >= len(expected)
```

### Remote E2E Test
```bash
# 1. Deploy test fixture
python scripts/deploy_fixture.py

# 2. Create PRs from changesets
python scripts/create_test_prs.py
# → Reads ALL_CHANGESETS
# → Creates 4 PRs automatically

# 3. Run evaluation
adk eval evalsets/test_fixture_prs.evalset.json
# → Tests agents on real GitHub PRs
# → Uses changeset expectations for validation
```

### Sequential Learning Test
```python
from capstone.changesets import ALL_CHANGESETS
from capstone.memory_bank import MemoryBank

memory = MemoryBank()
results = []

for i, changeset in enumerate(ALL_CHANGESETS):
    # Create PR from changeset
    pr_num = deploy_changeset_as_pr(changeset)
    
    # Review
    result = await orchestrator.review_pr(f".../{pr_num}")
    results.append(result)
    
    # Update memory
    await memory.update_from_review(result)

# Verify learning: later reviews should be faster/better
assert results[3].time < results[0].time
```

## Adding New Test Case

### Step 1: Define Changeset
```python
# changesets.py

CHANGESET_05_XSS_VULNERABILITY = Changeset(
    id="cs-05-xss",
    name="Add XSS Vulnerability",
    category=IssueCategory.SECURITY,
    difficulty="high",
    target_file="app/views.py",
    operation="add",
    new_content='''...code with XSS...''',
    expected_issues=[
        ExpectedIssue(
            type="xss",
            severity="high",
            file_path="app/views.py",
            line_start=10,
            description="Unescaped user input",
            must_detect=True
        )
    ],
    pr_title="Add user profile view",
    pr_body="...",
    branch_name="feature/user-profiles",
    min_issues_to_detect=1,
    max_false_positives=0,
    target_processing_time=30.0
)

ALL_CHANGESETS.append(CHANGESET_05_XSS_VULNERABILITY)
```

### Step 2: Add to Evalset
```json
{
  "id": "security-02",
  "changeset_id": "cs-05-xss",
  "name": "XSS Detection",
  "description": "Detect XSS vulnerability in user input"
}
```

### Step 3: Deploy
```bash
python scripts/create_test_prs.py
# → Automatically creates PR for CHANGESET_05

adk eval evalsets/test_fixture_prs.evalset.json
# → Tests agent on new PR
```

**That's it!** All three test modes automatically pick up the new changeset:
- ✅ Unit tests via `ALL_CHANGESETS`
- ✅ E2E tests via `create_test_prs.py`
- ✅ Learning tests via sequential runner

## Benefits

### 1. DRY Principle
- Define once, use everywhere
- No duplication between local and remote tests
- Update in one place → propagates automatically

### 2. Consistency
- Same test scenarios across all modes
- Same expected outcomes everywhere
- Reduces test maintenance burden

### 3. Fast Iteration
- Local tests: no network, instant feedback
- Remote tests: real integration validation
- Sequential tests: demonstrate improvement

### 4. Clear Expectations
- Expected issues documented with changeset
- Test criteria embedded (min issues, max FP, time)
- Easy to verify if test passes

### 5. Easy Extension
- Add changeset → works everywhere
- All test infrastructure already in place
- No need to update multiple files

## Test Modes Comparison

| Mode | Speed | Network | Git Required | Use Case |
|------|-------|---------|--------------|----------|
| **Unit** | ⚡ Fast | ❌ No | ❌ No | Quick validation, TDD |
| **Integration** | 🏃 Medium | ❌ No | ❌ No | Agent behavior testing |
| **E2E** | 🐢 Slow | ✅ Yes | ✅ Yes | Full system validation |
| **Sequential** | 🐌 Slowest | ✅ Yes | ✅ Yes | Memory Bank learning |

**All use same changeset definitions!**

## Implementation Status

✅ **Completed (Day 2):**
- `changesets.py` with 4 complete changesets
- `tools/diff_generator.py` for synthetic diffs
- `tools/mock_pr_context.py` for PullRequest objects
- `scripts/create_test_prs.py` updated to use changesets
- `evalsets/test_fixture_prs.evalset.json` linked to changesets
- `tests/test_changesets.py` comprehensive unit tests
- `docs/testing-strategy.md` complete documentation
- `evalsets/README.md` updated with changeset approach

⏳ **Remaining:**
- `tests/learning/sequential_runner.py` (sequential learning tests)
- Agent implementation to actually test
- Memory Bank implementation
- Deployment and real PR testing

## Related Documents

- `/src/capstone/docs/testing-strategy.md` - Complete testing guide
- `/src/capstone/evalsets/README.md` - Evaluation documentation
- `/src/capstone/changesets.py` - Changeset definitions (source)

---

**Last Updated:** November 19, 2025 (Day 2)  
**Next:** Begin Analyzer Agent implementation with git diff parsing
