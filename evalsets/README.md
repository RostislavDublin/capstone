# Quality Guardian - Integration Evaluation

Comprehensive ADK evalset for testing Quality Guardian agent end-to-end.

## Overview

This is an **integration test** that validates all workflows of the Quality Guardian system:
- Bootstrap (historical analysis)
- Sync (incremental updates)
- Query Trends (Firestore analytics)
- Query Root Cause (RAG semantic search)
- Composite Queries (multi-agent orchestration)
- Error Handling (invalid commands)

## Prerequisites

⚠️ **IMPORTANT:** This evalset requires a deployed test repository with real data.

### Required Setup

1. **Test Repository:** Configured in `.env`
   - Set `TEST_REPO_NAME` (repo name only, e.g., `quality-guardian-test-fixture`)
   - Owner automatically set to `RostislavDublin` in code
   - Alternatively: Use `TEST_FIXTURE_REPO` for full `owner/repo` format
   - Must exist on GitHub with at least 10 commits
   - Should contain auditable Python code

2. **Bootstrap Required:** Repository must be bootstrapped first
   ```bash
   # Bootstrap test repo before running evalset
   # (Uses TEST_REPO_NAME from .env)
   python demos/demo_quality_guardian_agent.py 2
   ```

3. **Environment Variables:**
   - `GITHUB_TOKEN` - GitHub API access
   - `GOOGLE_CLOUD_PROJECT` - GCP project ID
   - `GOOGLE_APPLICATION_CREDENTIALS` - Service account key

4. **GCP Resources:**
   - Firestore database (structured data)
   - Vertex AI RAG Corpus (semantic search)

## File

### `quality_guardian.evalset.json`

Single comprehensive evalset with 6 test cases:

| Test ID | Scenario | Expected Agent | What It Tests |
|---------|----------|----------------|---------------|
| 01_bootstrap | "Bootstrap repo and analyze 10 commits" | bootstrap_agent | Initial historical analysis |
| 02_sync | "Check for new commits" | sync_agent | Incremental updates |
| 03_query_trends | "Show quality trends" | query_orchestrator → trends_agent | Firestore analytics |
| 04_query_root_cause | "Why quality dropped?" | query_orchestrator → root_cause_agent | RAG semantic search |
| 05_query_composite | "Show trends AND explain why" | query_orchestrator → both agents | Multi-agent orchestration |
| 06_invalid_command | "Delete all commits" | (graceful rejection) | Error handling |

## Architecture Validated

```
User Query
    ↓
quality_guardian (Level 1 Dispatcher)
├─ transfer_to_agent pattern
├─ Routes to:
│  ├─ bootstrap_agent ──→ GitHub API + Bandit + Radon + Firestore + RAG
│  ├─ sync_agent ──────→ GitHub API + (same analysis pipeline)
│  └─ query_orchestrator (Level 2 Router)
│     ├─ AgentTool pattern
│     ├─ trends_agent ──→ Firestore (structured queries)
│     └─ root_cause_agent ──→ RAG Corpus (semantic search)
```

## Usage

### 1. Setup Test Repository

```bash
# Create test fixture repo (if not exists)
# Must have Python code with security issues, complexity variations

# Example commits needed:
# - Commits with SQL injection
# - Commits with high complexity
# - Commits with clean code
# - Mix of quality improvements and degradations
```

### 2. Bootstrap Repository

```bash
# Run bootstrap demo to populate Firestore + RAG
python demos/demo_quality_guardian_agent.py 2

# Or use agent directly
# User: "Bootstrap RostislavDublin/<TEST_REPO_NAME>, last 10 commits"
```

### 3. Run Evalset

```bash
adk eval evalsets/quality_guardian.evalset.json
```

### Expected Output

```
✅ 01_bootstrap: PASS
   - Routed to bootstrap_agent
   - Returns audit summary
   - Contains: "commits", "audited", "security"

✅ 02_sync: PASS
   - Routed to sync_agent
   - Reports new commits or "up to date"

✅ 03_query_trends: PASS
   - Routed to query_orchestrator
   - Returns trend analysis from Firestore

✅ 04_query_root_cause: PASS
   - Routed to query_orchestrator
   - Returns RAG-powered root cause analysis

✅ 05_query_composite: PASS
   - Routed to query_orchestrator
   - Returns merged response (trends + root cause)

✅ 06_invalid_command: PASS
   - Gracefully rejects with error message
```

## What This Tests

### 1. Routing Logic (LLM-Driven Delegation)
- Does guardian correctly identify intent?
- Bootstrap queries → bootstrap_agent
- Sync queries → sync_agent
- All other queries → query_orchestrator

### 2. Multi-Agent Orchestration
- Does orchestrator route single queries to correct agent?
- Does orchestrator call BOTH agents for composite queries?
- Are responses properly merged?

### 3. Tool Integration
- GitHub API (repository access)
- Bandit (security scanning)
- Radon (complexity analysis)
- Firestore (structured queries)
- RAG Corpus (semantic search)

### 4. ADK Patterns
- `transfer_to_agent` (Level 1 → Level 2)
- `AgentTool` (Level 2 → Level 3)
- Parallel agent execution (composite queries)

### 5. Error Handling
- Invalid commands rejected gracefully
- Helpful error messages
- No crashes or undefined behavior

## What This Does NOT Test

❌ **Query Result Accuracy** - Use unit/integration tests for this
❌ **RAG Retrieval Quality** - Use RAG-specific tests
❌ **GitHub API Edge Cases** - Use connector tests
❌ **Performance/Latency** - Use benchmark tests

**Focus:** End-to-end agent flow and routing correctness.

## Troubleshooting

### Test Fails: "Repository not found"
**Cause:** Test repo doesn't exist or not accessible
**Fix:** 
```bash
# Verify token has access to your test repo
# Replace with your owner/repo
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/RostislavDublin/$TEST_REPO_NAME
```

### Test Fails: "No audits found"
**Cause:** Repository not bootstrapped
**Fix:**
```bash
# Bootstrap before running evalset
python demos/demo_quality_guardian_agent.py 2
```

### Test Fails: "RAG corpus not found"
**Cause:** Vertex AI RAG not configured
**Fix:**
```bash
# Check RAG corpus exists
python -c "from src.storage.rag_corpus import RAGCorpusManager; \
  mgr = RAGCorpusManager(); print(mgr.get_or_create_corpus())"
```

### Test Times Out
**Cause:** Bootstrap/Sync analyzing too many commits
**Fix:** Reduce commits in test case (10 → 5)

### All Tests Pass but Empty Responses
**Cause:** Agents route correctly but tools fail silently
**Fix:** Check logs for tool execution errors

## Integration with CI/CD

**Recommendation:** Do NOT run in CI/CD pipeline

**Reasons:**
- Requires real GitHub repository (not mockable)
- Requires GCP credentials (security risk)
- Requires Firestore + RAG (infrastructure dependency)
- Slow (30-60 seconds per test case)

**Alternative:** Use unit/integration tests in CI, run evalset manually before releases.

## When to Run This Evalset

✅ **Before competition submission** - Validate everything works end-to-end
✅ **After major agent refactoring** - Ensure routing still correct
✅ **Before production deployment** - Final smoke test
✅ **When debugging agent behavior** - Isolate which workflow breaks

❌ **In CI/CD** - Too slow, too many dependencies
❌ **During development** - Use demos instead
❌ **For unit testing** - Use pytest tests

## Expected Timing

- 01_bootstrap: ~15-30 seconds (depends on commits)
- 02_sync: ~5-10 seconds
- 03_query_trends: ~3-5 seconds (Firestore fast)
- 04_query_root_cause: ~5-10 seconds (RAG retrieval)
- 05_query_composite: ~8-15 seconds (both agents)
- 06_invalid_command: ~1-2 seconds

**Total:** ~40-70 seconds for full evalset

## Success Criteria

**All 6 tests must pass:**
- ✅ Correct agent routing (validates `tool_uses`)
- ✅ Non-empty responses
- ✅ Contains expected keywords
- ✅ Completes within reasonable time

**Single failure = integration broken**

## Maintenance

When agent structure changes:
1. Update `tool_uses[].name` to match new agent names
2. Update `expected_response.contains` keywords
3. Update README architecture diagram
4. Re-run evalset to validate changes

When test repo changes:
1. Re-bootstrap repository
2. Update commit counts in test cases
3. Verify all workflows still work

---

**Last Updated:** December 1, 2025  
**Status:** Production-ready integration test for Quality Guardian v1.0
