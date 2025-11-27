# Firestore Integration Plan

## Phase 1: Setup & Basic Repository (30 min)
**Goal:** Basic infrastructure works

- [ ] 1. Add `google-cloud-firestore` to requirements/base.txt
- [ ] 2. Update config with Firestore settings (src/config.py)
- [ ] 3. Create `src/storage/firestore_client.py` with basic CRUD
- [ ] 4. Write unit tests (tests/unit/test_firestore_client.py)
- [ ] 5. Run tests → all pass

**Deliverable:** `FirestoreAuditDB` class with `store_commit_audit()`, `get_repositories()`, `query_by_repository()`

---

## Phase 2: Integration Tests (20 min)
**Goal:** Real Firestore integration works

- [ ] 1. Create `tests/integration/test_firestore_integration.py`
- [ ] 2. Test: store → retrieve → verify
- [ ] 3. Test: multiple repos, multiple commits
- [ ] 4. Run integration test with real Firestore
- [ ] 5. Verify data in Firestore console

**Deliverable:** Verified real Firestore operations

---

## Phase 3: Tool Integration (20 min)
**Goal:** Tools use Firestore

- [ ] 1. Update `analyze_repository()` → dual write (Firestore + RAG)
- [ ] 2. Update `list_analyzed_repositories()` → read from Firestore
- [ ] 3. Update unit tests for tools
- [ ] 4. Run tests → all pass
- [ ] 5. NOT touching `query_trends()` yet

**Deliverable:** Bootstrap and List work via Firestore

---

## Phase 4: Demo Validation (15 min)
**Goal:** Demo works with Firestore

- [ ] 1. Run demo → Bootstrap creates Firestore entries
- [ ] 2. Verify: "List repos" returns correct list
- [ ] 3. Check Firestore console → see documents
- [ ] 4. Query trends still not working (expected)

**Deliverable:** Partially working solution (Bootstrap + List)

---

## Phase 5: Query Trends Refactoring (30 min)
**Goal:** Query trends uses Firestore + RAG

- [ ] 1. Refactor `query_trends()`: fetch from Firestore first
- [ ] 2. Pass fetched commits to Gemini with RAG grounding
- [ ] 3. Update tests
- [ ] 4. Run full demo → everything works end-to-end

**Deliverable:** Fully working system

---

## Firestore Collection Structure

```
repositories/
  └─ {owner}_{repo}/                    (document)
      ├─ name: "owner/repo"
      ├─ total_commits: N
      ├─ first_analyzed: Timestamp
      └─ last_analyzed: Timestamp
      
      commits/                          (subcollection)
        └─ {commit_sha}/                (document)
            ├─ sha: "abc123"
            ├─ timestamp: Timestamp
            ├─ author: "john@example.com"
            ├─ commit_message: "..."
            └─ ... (full CommitAudit JSON)

file_audits/                            (top-level collection)
  └─ {owner}_{repo}_{file_path_sanitized}/ (document)
      ├─ repository: "owner/repo"
      ├─ file_path: "src/auth.py"
      ├─ first_seen: Timestamp
      └─ last_modified: Timestamp
      
      audits/                           (subcollection)
        └─ {commit_sha}/                (document)
            ├─ commit_sha: "abc123"
            ├─ is_baseline: true/false
            └─ ... (file-specific audit data)
```

---

## Current Status

### Completed:
- None yet

### In Progress:
- Phase 1, Step 1: Adding google-cloud-firestore dependency

### Next:
- Add dependency to requirements/base.txt
- Install in venv
- Request user validation before proceeding
