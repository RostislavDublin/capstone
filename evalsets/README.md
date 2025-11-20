# Evaluation Sets

This directory contains ADK evaluation datasets for testing agent performance using unified changeset definitions.

## Architecture

```
changesets.py                    # Source of truth
    ↓
evalset references changesets    # via changeset_id
    ↓
adk eval                         # Tests agents on real PRs
```

## Files

- `test_fixture_prs.evalset.json` - Test cases referencing changeset definitions

## Changeset-Based Evaluation

All test cases reference changesets from `changesets.py`:

```json
{
  "id": "security-01",
  "changeset_id": "cs-01-sql-injection",
  "name": "SQL Injection Detection"
}
```

### Benefits

- **Single source of truth**: Changesets define expectations once
- **Consistent tests**: Same definitions for local and remote testing
- **Easy maintenance**: Update changeset, all tests reflect changes
- **Comprehensive**: Test criteria embedded in changeset definitions

## Usage

### Remote E2E Evaluation

```bash
# Deploy fixture and create PRs first
python scripts/deploy_fixture.py
python scripts/create_test_prs.py

# Run evaluation against real GitHub PRs
adk eval evalsets/test_fixture_prs.evalset.json
```

### Local Evaluation

```python
# Use changesets directly for unit tests
from capstone.changesets import CHANGESET_01_SQL_INJECTION
from capstone.tools.diff_generator import generate_diff_from_changeset

# Generate synthetic diff
diff = generate_diff_from_changeset(CHANGESET_01_SQL_INJECTION)

# Test agent
result = await agent.analyze_diff(diff)

# Verify against changeset expectations
assert result.critical_issues >= 2
```

## Test Cases

### 1. security-01 → cs-01-sql-injection
**Category:** Security  
**Expected Issues:**
- 🚨 Critical: SQL injection vulnerability
- 🚨 Critical: Plaintext password storage
- ⚠️ High: Missing rate limiting
- 💡 Medium: No input validation

**Validation:**
- Must detect both critical issues
- Max 0 false positives
- Target time: 30 seconds

### 2. complexity-01 → cs-02-high-complexity
**Category:** Complexity  
**Expected Issues:**
- ⚠️ High: Cyclomatic complexity 25
- ⚠️ High: 7 levels of nesting
- ⚠️ High: Duplicate logic
- 💡 Medium: No error handling
- 💡 Medium: Function too long

**Validation:**
- Must detect complexity issue
- Max 1 false positive
- Target time: 45 seconds

### 3. style-01 → cs-03-style-violations
**Category:** Style  
**Expected Issues:**
- 💡 Medium: PascalCase function names
- 💡 Medium: Missing docstrings
- 💡 Medium: No type hints
- 💡 Medium: Line length violations
- 💡 Medium: Multiple statements per line
- 💡 Medium: Bad variable naming
- 💡 Medium: Import inside function
- 💡 Medium: Inconsistent spacing

**Validation:**
- Must detect at least 5 style issues
- Max 2 false positives
- Target time: 20 seconds

### 4. control-01 → cs-04-clean-code
**Category:** None (Control)  
**Expected Issues:** None - clean code

**Validation:**
- Should detect 0 issues
- Validates false positive rate
- Target time: 15 seconds

## Evaluation Criteria

Each test case validates:

1. **Accuracy**: Issue detection vs expectations
2. **False Positives**: Issues detected that shouldn't exist
3. **Performance**: Processing time vs target
4. **Completeness**: Must-detect issues found
5. **Severity**: Correct severity classification

## Adding New Test Cases

### Step 1: Define Changeset

```python
# changesets.py
CHANGESET_05_XSS = Changeset(
    id="cs-05-xss",
    name="XSS Vulnerability",
    expected_issues=[...],
    min_issues_to_detect=1,
    max_false_positives=0,
    target_processing_time=30.0
)
```

### Step 2: Add to Evalset

```json
{
  "id": "security-02",
  "changeset_id": "cs-05-xss",
  "name": "XSS Detection",
  "description": "Detect XSS vulnerability in user input handling"
}
```

### Step 3: Deploy

```bash
# Changeset automatically creates PR
python scripts/create_test_prs.py

# Run evaluation
adk eval evalsets/test_fixture_prs.evalset.json
```

## Sequential Learning Evaluation

Test Memory Bank improvement:

```bash
# Run sequential reviews to test learning
python tests/learning/sequential_runner.py

# Generates metrics:
# - Review 1: Baseline performance
# - Review 2: Using patterns from Review 1
# - Review 3: Using patterns from Reviews 1-2
# - Review 4: Using patterns from Reviews 1-3
```

Expected improvements:
- ⚡ Faster processing (pattern reuse)
- 🎯 Better accuracy (learned patterns)
- 📈 More context (accumulated standards)
