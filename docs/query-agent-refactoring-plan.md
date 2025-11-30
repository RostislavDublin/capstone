# Query Agent Refactoring Plan

**Goal:** Transform monolithic `query_agent` into orchestrator with specialized sub-agents.

**Status:** Planning (Nov 29, 2025)

---

## 🎯 Problem Statement

**Current Architecture:**
```
query_agent
├── query_trends(repo, question) [universal tool]
└── list_analyzed_repositories()
```

**Issues:**
1. **Single tool tries to do everything:** trends, patterns, authors, files, metrics
2. **Complex instructions:** Agent must understand 5+ different query types
3. **Unclear routing:** Gemini decides what data to extract from one big prompt
4. **Hard to test:** Can't test each capability independently
5. **RAG API bug:** Uses deprecated `similarity_top_k` parameter

**Impact:**
- TEST 3 fails in main demo (TypeError on RAG API)
- Agent gives vague answers (not enough structure)
- Hard to add new query types

---

## 🏗️ Target Architecture

```
quality_guardian (root orchestrator)
├── bootstrap_agent
├── sync_agent
└── query_agent (query orchestrator)
    ├── trends_agent       # Quality trend analysis
    ├── patterns_agent     # Issue pattern detection
    ├── authors_agent      # Author quality statistics
    ├── files_agent        # Problematic files (hotspots)
    └── metrics_agent      # Specific numeric metrics
```

**Benefits:**
1. **Specialized experts:** Each sub-agent knows exactly what to do
2. **Simple instructions:** Short, focused prompts for each agent
3. **Specialized tools:** Each tool does one thing well (Firestore + targeted RAG)
4. **Independent testing:** Test each query type separately
5. **Incremental development:** Add sub-agents one by one

---

## 📋 Implementation Plan

### Phase 0: Setup Query Orchestrator (Empty Shell)

**Goal:** Create orchestrator structure without breaking existing functionality.

**Tasks:**
- [ ] Create `src/agents/query_orchestrator/` directory
- [ ] Create empty orchestrator agent with routing instructions
- [ ] Keep old `query_agent` as fallback
- [ ] Update `quality_guardian` to use orchestrator (optional at this stage)
- [ ] Verify demo still works with old query_agent

**Files:**
```
src/agents/query_orchestrator/
├── __init__.py
└── agent.py         # Empty orchestrator, no sub-agents yet
```

**Deliverable:** Orchestrator exists but does nothing yet.

---

### Phase 1: Trends Agent (Priority 1)

**Goal:** Fix TEST 3 - most critical user-facing feature.

#### 1.1 Create Tool: `query_trends(repo)`

**Location:** `src/tools/query_tools.py` (new file)

**Function:**
```python
def query_trends(repo: str) -> dict:
    """Analyze quality trends: improving/stable/degrading.
    
    Returns:
        {
            "trend_direction": "IMPROVING" | "STABLE" | "DEGRADING",
            "recent_avg": 87.5,
            "historical_avg": 82.3,
            "delta": +5.2,
            "commits_analyzed": 20,
            "data_sample": [...],  # Recent 5 commits
        }
    """
```

**Data Source:** Firestore only (no RAG for MVP)
- Get last 50 commits ordered by date
- Calculate recent avg (last 5) vs historical avg (6-10)
- Determine trend direction (threshold: ±2 points)
- Return structured data

**Success Criteria:**
- [ ] Tool returns correct trend direction
- [ ] Math is accurate (recent vs historical)
- [ ] No RAG dependency (Firestore only)

#### 1.2 Create Agent: `trends_agent`

**Location:** `src/agents/query_orchestrator/trends/agent.py`

**Instructions:**
```
You are a Quality Trend Analyst.

Tool: query_trends(repo)
Returns: trend_direction, scores, data_sample

Your task:
1. Call query_trends(repo)
2. Present findings:
   - TREND: IMPROVING/STABLE/DEGRADING
   - Recent avg: X/100
   - Historical avg: Y/100
   - Data sample: 5 commits with SHAs, dates, scores
3. Explain what's driving the trend

Be specific. Show your math. Cite commit SHAs.
```

**Success Criteria:**
- [ ] Agent calls tool correctly
- [ ] Response includes all required fields
- [ ] Explanation is actionable

#### 1.3 Integrate into Orchestrator

**Update:** `src/agents/query_orchestrator/agent.py`

**Add routing:**
```python
tools=[
    AgentTool(agent=trends_agent),
]

instruction="""
Route user questions:
- "trends", "improving", "degrading", "quality direction" → trends_agent
- All other questions → respond "Not implemented yet, stay tuned!"
"""
```

**Success Criteria:**
- [ ] Orchestrator routes "trends" questions to trends_agent
- [ ] TEST 3 passes in main demo
- [ ] Other questions get polite "not implemented" message

---

### Phase 2: Patterns Agent (Priority 2)

**Goal:** Identify most common issues (security, complexity).

#### 2.1 Create Tool: `query_patterns(repo)`

**Function:**
```python
def query_patterns(repo: str) -> dict:
    """Get most common issue patterns.
    
    Returns:
        {
            "top_patterns": [
                {"type": "SQL_INJECTION", "count": 15, "severity": "critical"},
                {"type": "COMPLEXITY_HIGH", "count": 12, "severity": "medium"},
                ...
            ],
            "security_total": 23,
            "complexity_total": 18,
            "examples": [...],  # Optional: from RAG
        }
    """
```

**Data Source:** 
- Primary: Firestore (issue types aggregation)
- Secondary: RAG (semantic search for specific examples)

**Success Criteria:**
- [ ] Aggregates issues by type from Firestore
- [ ] Returns top 5 patterns
- [ ] Includes severity levels

#### 2.2 Create Agent: `patterns_agent`

**Location:** `src/agents/query_orchestrator/patterns/agent.py`

**Instructions:**
```
You are an Issue Pattern Analyst.

Tool: query_patterns(repo)
Returns: top_patterns, counts, examples

Present findings:
1. Top 3-5 issue patterns
2. Frequency and severity
3. Security vs complexity breakdown
4. Actionable recommendations
```

#### 2.3 Update Orchestrator Routing

**Add to routing rules:**
- "patterns", "common issues", "what problems", "issue types" → patterns_agent

**Success Criteria:**
- [ ] Patterns questions routed correctly
- [ ] Agent returns top patterns with counts
- [ ] Recommendations are specific

---

### Phase 3: Authors Agent (Priority 3)

**Goal:** Show who writes best/worst quality code.

#### 3.1 Create Tool: `query_authors(repo)`

**Function:**
```python
def query_authors(repo: str) -> dict:
    """Get author quality statistics.
    
    Returns:
        {
            "authors": [
                {"name": "Alice", "commits": 15, "avg_quality": 92.5},
                {"name": "Bob", "commits": 8, "avg_quality": 78.3},
                ...
            ],
            "best_author": "Alice",
            "needs_help": ["Bob"],
        }
    """
```

**Data Source:** Firestore (group by author, avg quality_score)

**Success Criteria:**
- [ ] Groups commits by author
- [ ] Calculates average quality per author
- [ ] Identifies best/worst performers

#### 3.2 Create Agent: `authors_agent`

**Location:** `src/agents/query_orchestrator/authors/agent.py`

**Instructions:**
```
You are a Code Quality Mentor.

Tool: query_authors(repo)
Returns: author stats, best/worst performers

Present findings:
1. Best authors (highest avg quality)
2. Authors needing mentoring
3. Commit volume vs quality correlation
4. Mentoring recommendations
```

#### 3.3 Update Orchestrator Routing

**Add to routing rules:**
- "authors", "who writes", "best code", "worst code" → authors_agent

---

### Phase 4: Files Agent (Priority 4)

**Goal:** Identify hotspots (files with most issues).

#### 4.1 Create Tool: `query_files(repo)`

**Function:**
```python
def query_files(repo: str) -> dict:
    """Get problematic files (hotspots).
    
    Returns:
        {
            "hotspots": [
                {"file": "app/main.py", "issues": 12, "severity": "high"},
                {"file": "utils/db.py", "issues": 8, "severity": "medium"},
                ...
            ],
            "refactoring_candidates": [...],
        }
    """
```

**Data Source:** 
- Primary: Firestore (file_path from issues)
- Secondary: RAG (semantic search for file context)

**Success Criteria:**
- [ ] Extracts file paths from CommitAudit.issues
- [ ] Aggregates issues per file
- [ ] Returns top 10 hotspots

#### 4.2 Create Agent: `files_agent`

**Location:** `src/agents/query_orchestrator/files/agent.py`

**Instructions:**
```
You are a Refactoring Advisor.

Tool: query_files(repo)
Returns: hotspot files, issue counts

Present findings:
1. Top 5-10 problematic files
2. Issue counts and severity
3. Refactoring priority (critical first)
4. Specific recommendations per file
```

#### 4.3 Update Orchestrator Routing

**Add to routing rules:**
- "files", "hotspots", "refactoring", "problematic files" → files_agent

---

### Phase 5: Metrics Agent (Priority 5)

**Goal:** Answer specific numeric questions.

#### 5.1 Create Tool: `query_metrics(repo, metric_type)`

**Function:**
```python
def query_metrics(repo: str, metric_type: str = "all") -> dict:
    """Get specific numeric metrics.
    
    Args:
        metric_type: "critical_count" | "avg_quality" | "severity_breakdown" | "all"
    
    Returns:
        {
            "critical_issues": 5,
            "high_issues": 12,
            "medium_issues": 23,
            "low_issues": 8,
            "avg_quality_score": 85.2,
            "total_commits": 47,
        }
    """
```

**Data Source:** Firestore (direct aggregations)

**Success Criteria:**
- [ ] Returns exact numbers (no vague answers)
- [ ] Supports different metric types
- [ ] Fast (no RAG, pure Firestore)

#### 5.2 Create Agent: `metrics_agent`

**Location:** `src/agents/query_orchestrator/metrics/agent.py`

**Instructions:**
```
You are a Metrics Reporter.

Tool: query_metrics(repo, metric_type)
Returns: precise numbers

Your answers must be:
1. SPECIFIC: "5 critical issues", not "several issues"
2. COMPLETE: Show breakdown (critical/high/medium/low)
3. CONTEXTUAL: Compare to average if relevant
4. BRIEF: Numbers first, explanation second
```

#### 5.3 Update Orchestrator Routing

**Add to routing rules:**
- "how many", "count", "average", "metrics", "numbers" → metrics_agent

---

## 📊 Success Criteria (Overall)

### Functional Requirements
- [ ] All 5 sub-agents implemented and working
- [ ] Query orchestrator routes correctly
- [ ] Main demo TEST 3 passes
- [ ] Each query type returns structured, actionable data

### Technical Requirements
- [ ] No deprecated RAG API calls (`similarity_top_k`)
- [ ] Firestore as primary data source (deterministic)
- [ ] RAG used only for semantic details (examples, context)
- [ ] Each tool has unit tests
- [ ] Each agent has e2e tests

### Quality Requirements
- [ ] Agent responses are specific (no vague answers)
- [ ] Math is correct (trend calculations)
- [ ] Recommendations are actionable
- [ ] Response times < 5 seconds per query

---

## 🧪 Testing Strategy

### Unit Tests (per tool)
```python
# tests/unit/test_query_tools.py
def test_query_trends_improving():
    """Test trend calculation when quality improves."""
    
def test_query_patterns_aggregation():
    """Test issue pattern grouping."""
    
def test_query_authors_stats():
    """Test author quality calculations."""
```

### Integration Tests (per agent)
```python
# tests/integration/test_trends_agent.py
@pytest.mark.asyncio
async def test_trends_agent_response():
    """Test trends_agent with mock Firestore data."""
```

### E2E Tests (full flow)
```python
# tests/e2e/test_query_orchestrator.py
@pytest.mark.asyncio
async def test_orchestrator_routes_trends():
    """Test orchestrator routes trends questions."""
```

### Demo Validation
```bash
# Main demo must pass all 4 tests
python ./demos/demo_quality_guardian_agent.py 1

# TEST 3 specifically:
# User: "Show quality trends for repo"
# Expected: Trend direction, scores, data sample
```

---

## 📁 File Structure (Final)

```
src/
├── agents/
│   ├── bootstrap/
│   │   └── agent.py
│   ├── sync/
│   │   └── agent.py
│   ├── query/                    # OLD (keep for reference)
│   │   └── agent.py
│   ├── query_orchestrator/       # NEW
│   │   ├── __init__.py
│   │   ├── agent.py              # Orchestrator
│   │   ├── trends/
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   ├── patterns/
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   ├── authors/
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   ├── files/
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   └── metrics/
│   │       ├── __init__.py
│   │       └── agent.py
│   └── quality_guardian/
│       └── agent.py              # Root orchestrator
├── tools/
│   ├── repository_tools.py       # bootstrap/sync tools
│   └── query_tools.py            # NEW: all query tools
└── storage/
    ├── firestore_client.py       # Primary data source
    └── rag_corpus.py             # Secondary (semantic search)
```

---

## 🚀 Rollout Plan

### Week 1: Foundation
- **Day 1:** Phase 0 (empty orchestrator) + Phase 1.1 (trends tool)
- **Day 2:** Phase 1.2-1.3 (trends agent + integration)
- **Day 3:** Validate TEST 3 passes, fix bugs

### Week 2: Core Analytics
- **Day 4:** Phase 2 (patterns agent)
- **Day 5:** Phase 3 (authors agent)
- **Day 6:** Phase 4 (files agent)

### Week 3: Polish
- **Day 7:** Phase 5 (metrics agent)
- **Day 8:** Integration testing, bug fixes
- **Day 9:** Update documentation, demos
- **Day 10:** Final validation, deployment

---

## 🎯 Migration Strategy

### Backward Compatibility
- Keep old `query_agent` in `src/agents/query/` (deprecated)
- Add deprecation notice in code
- Update `quality_guardian` to use `query_orchestrator`
- Remove old agent only after full validation

### Rollback Plan
If orchestrator fails:
1. Revert `quality_guardian` to use old `query_agent`
2. Fix orchestrator offline
3. Re-deploy when ready

---

## 📝 Notes

**Design Principles:**
1. **Incremental:** Add one sub-agent at a time
2. **Testable:** Each component tested independently
3. **Reversible:** Can rollback to old agent if needed
4. **Pragmatic:** Firestore first, RAG for details only

**Open Questions:**
- Should orchestrator have its own tools (e.g., `list_analyzed_repositories()`)?
  - **Decision:** Yes, keep utility tools at orchestrator level
- Should sub-agents be able to call each other?
  - **Decision:** No, keep it simple (orchestrator routes only)
- What if user asks complex multi-faceted question?
  - **Decision:** Orchestrator can call multiple sub-agents sequentially

**Future Enhancements (Post-MVP):**
- Comparison agent (compare two repos)
- Regression agent (detect quality regressions)
- Prediction agent (predict future quality trends)
- Recommendation agent (personalized improvement plans)

---

## ✅ Definition of Done

Query Agent refactoring is complete when:
1. All 5 sub-agents implemented
2. All tests passing (unit, integration, e2e)
3. Main demo TEST 3 passes
4. Documentation updated
5. Old query_agent deprecated (marked, not deleted)
6. Performance acceptable (<5s per query)
7. Code reviewed and committed

**Target Completion:** December 6, 2025 (1 week from now)
