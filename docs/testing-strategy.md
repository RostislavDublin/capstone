# Testing Strategy

Complete testing infrastructure for AI Code Review Orchestration System with unified changeset definitions for local and remote testing.

## Architecture Overview

```
changesets.py                    # Source of truth - changeset definitions
    ↓
    ├─→ Local Testing            # Unit/Integration tests
    ├─→ Remote E2E Testing       # GitHub PRs
    └─→ Sequential Learning      # Memory Bank evaluation
```

## Changeset-Driven Testing

All tests use **unified changeset definitions** from `changesets.py`:

```python
from capstone.changesets import CHANGESET_01_SQL_INJECTION

# Changeset contains:
# - Code changes (new_content or patch)
# - Expected issues with severity
# - Test criteria (min issues, max false positives)
# - PR metadata (title, body, branch)
```

---

## 1. Local Testing (No GitHub Required)

### Unit Tests: Individual Components

**Test tools in isolation:**

```python
# tests/unit/test_security_scanner.py
from capstone.changesets import CHANGESET_01_SQL_INJECTION
from capstone.tools.security_scanner import scan_code

def test_sql_injection_detection():
    """Test security scanner finds SQL injection."""
    # Get code with SQL injection from changeset
    code = CHANGESET_01_SQL_INJECTION.new_content
    
    # Scan
    issues = scan_code(code, file_path="app/auth.py")
    
    # Verify using changeset expected issues
    expected = CHANGESET_01_SQL_INJECTION.expected_issues
    assert len([i for i in issues if i.type == "sql_injection"]) >= 1
    assert issues[0].severity == "critical"
```

**Generate synthetic diffs:**

```python
# tests/unit/test_diff_parser.py
from capstone.changesets import CHANGESET_01_SQL_INJECTION
from capstone.tools.diff_generator import generate_diff

def test_parse_addition_diff():
    """Test parsing file addition diff."""
    # Generate diff from changeset
    diff = generate_diff(
        operation="add",
        file_path=CHANGESET_01_SQL_INJECTION.target_file,
        new_content=CHANGESET_01_SQL_INJECTION.new_content
    )
    
    # Parse
    parsed = parse_diff(diff)
    assert parsed.operation == "add"
    assert len(parsed.changes) > 0
```

### Integration Tests: Agent Behavior

**Test agents with mock data:**

```python
# tests/integration/test_analyzer_agent.py
from capstone.changesets import ALL_CHANGESETS
from capstone.agents import AnalyzerAgent
from capstone.tools.diff_generator import generate_diff

async def test_analyzer_on_all_changesets():
    """Test Analyzer Agent on all defined changesets."""
    agent = AnalyzerAgent()
    
    for changeset in ALL_CHANGESETS:
        # Generate diff from changeset
        diff = generate_diff(
            operation=changeset.operation,
            file_path=changeset.target_file,
            new_content=changeset.new_content,
            patch=changeset.patch
        )
        
        # Analyze
        result = await agent.analyze_diff(diff)
        
        # Verify against changeset expectations
        critical_issues = [i for i in result.issues if i.severity == "critical"]
        expected_critical = [i for i in changeset.expected_issues if i.severity == "critical"]
        
        assert len(critical_issues) >= len(expected_critical)
```

**Run:** `pytest tests/unit tests/integration`

---

## 2. Remote E2E Testing (GitHub Required)

### Setup: Deploy Test Fixture

```bash
# Deploy test fixture to GitHub
python scripts/deploy_fixture.py

# Create PRs from changesets
python scripts/create_test_prs.py
```

**What happens:**
1. `deploy_fixture.py` → creates `RostislavDublin/code-review-test-fixture`
2. `create_test_prs.py` → reads `changesets.py` → creates branches + PRs
3. Each PR applies one changeset

### E2E Tests: Full System

**Test complete review workflow:**

```python
# tests/e2e/test_full_review.py
from capstone.changesets import CHANGESET_01_SQL_INJECTION, get_changeset
from capstone.orchestrator import ReviewOrchestrator

async def test_review_sql_injection_pr():
    """E2E test: Review PR with SQL injection."""
    changeset = CHANGESET_01_SQL_INJECTION
    
    # Get PR from GitHub (created by create_test_prs.py)
    pr_url = f"https://github.com/RostislavDublin/code-review-test-fixture/pull/1"
    
    # Run full review
    orchestrator = ReviewOrchestrator()
    result = await orchestrator.review_pr(pr_url)
    
    # Verify using changeset expectations
    assert result.total_issues >= changeset.min_issues_to_detect
    assert count_false_positives(result) <= changeset.max_false_positives
    assert result.total_time < changeset.target_processing_time
    
    # Verify critical issues found
    must_detect = [i for i in changeset.expected_issues if i.must_detect]
    for expected in must_detect:
        assert any(i.type == expected.type for i in result.issues)
```

**Run with evalset:**

```bash
# Uses evalset that references changesets
adk eval evalsets/test_fixture_prs.evalset.json
```

---

## 3. Sequential Learning Tests (Memory Bank)

### Test: Agent Improves Over Time

**Stateful test with Memory Bank:**

```python
# tests/learning/test_sequential_review.py
from capstone.changesets import ALL_CHANGESETS
from capstone.memory_bank import MemoryBank
from capstone.orchestrator import ReviewOrchestrator

async def test_agent_learns_from_reviews():
    """Test that agent gets faster and smarter with experience."""
    
    # Setup
    memory_bank = MemoryBank()
    memory_bank.clear()  # Start fresh
    
    orchestrator = ReviewOrchestrator(memory_bank=memory_bank)
    
    results = []
    
    for i, changeset in enumerate(ALL_CHANGESETS, 1):
        # Deploy changeset as PR
        pr_number = deploy_changeset_as_pr(changeset, pr_number=i)
        
        # Review PR
        result = await orchestrator.review_pr(
            f"RostislavDublin/code-review-test-fixture/pull/{pr_number}"
        )
        
        results.append({
            "changeset": changeset.id,
            "time": result.total_time,
            "issues": result.total_issues,
            "patterns_used": len(result.context_output.patterns)
        })
        
        # Update memory
        await memory_bank.update_from_review(result)
    
    # Verify learning
    # 1. Time should decrease (agent gets faster)
    assert results[1]["time"] < results[0]["time"]
    
    # 2. Patterns accumulate
    assert results[2]["patterns_used"] > results[0]["patterns_used"]
    
    # 3. Accuracy improves
    assert calculate_accuracy(results[-1]) >= calculate_accuracy(results[0])
```

**Automation script:**

```bash
# scripts/run_learning_test.sh

# 1. Reset everything
python scripts/reset_fixture.py --yes
rm -rf memory_bank/

# 2. Deploy base fixture
python scripts/deploy_fixture.py

# 3. Run sequential reviews
python tests/learning/sequential_runner.py

# 4. Generate learning metrics report
python tests/learning/analyze_results.py
```

---

## 4. Test Fixture Management

### Current State (Baseline)

**test-fixture/** contains frozen bad code:
- `app/config.py` - hardcoded secrets
- `app/database.py` - SQL injection vulnerabilities  
- `app/utils.py` - high complexity
- `app/main.py` - security issues

**Never changes** - serves as baseline for all changesets.

### Changesets (Modifications)

**changesets.py** defines code changes:
- Add new files with issues
- Modify existing files
- Apply patches

### Deployment Process

```
test-fixture/       (baseline code)
      +
changesets.py       (modifications)
      ↓
deploy_fixture.py   (applies changesets to branches)
      ↓
GitHub repo         (base + branches + PRs)
```

---

## 5. Running Tests

### Quick Local Tests
```bash
# Unit tests (fast, no network)
pytest tests/unit -v

# Integration tests (mock GitHub)
pytest tests/integration -v
```

### Full E2E Tests
```bash
# Requires GitHub setup
export GITHUB_TOKEN=your_token

# Deploy fixture
python scripts/deploy_fixture.py

# Create PRs
python scripts/create_test_prs.py

# Run E2E
pytest tests/e2e -v
```

### Learning Tests
```bash
# Sequential evaluation
./scripts/run_learning_test.sh
```

### ADK Evaluation
```bash
# Uses changesets via evalset
adk eval evalsets/test_fixture_prs.evalset.json
```

---

## 6. Adding New Test Cases

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
            description="Unescaped user input in HTML",
            must_detect=True
        )
    ],
    pr_title="Add user profile view",
    pr_body="...",
    branch_name="feature/user-profiles",
    min_issues_to_detect=1,
    max_false_positives=0
)

ALL_CHANGESETS.append(CHANGESET_05_XSS_VULNERABILITY)
```

### Step 2: Add to Evalset

```json
{
  "id": "security-02",
  "changeset_id": "cs-05-xss",
  "name": "XSS Detection",
  ...
}
```

### Step 3: Tests Automatically Work

All three test modes automatically pick up the new changeset:
- ✅ Unit tests via `ALL_CHANGESETS`
- ✅ E2E tests via `create_test_prs.py`
- ✅ Learning tests via sequential runner

---

## 7. Benefits of Unified Approach

### Single Source of Truth
- One definition → multiple uses
- No duplication between local/remote tests
- Consistent expected outcomes

### Easy Maintenance
- Add changeset once
- Works everywhere
- Update expectations in one place

### Comprehensive Coverage
- Same scenarios tested locally and remotely
- Sequential tests build on same changesets
- Evalsets reference same definitions

### Flexibility
- Local tests: fast iteration
- Remote tests: real integration
- Learning tests: measure improvement

---

## Summary

**Changesets.py** = Central registry of test scenarios

**Local** = Fast, no network, synthetic diffs

**Remote** = Real PRs, full integration

**Sequential** = Memory Bank learning evaluation

**All use same definitions** = Consistency + maintainability
