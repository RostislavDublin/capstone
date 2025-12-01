# Capstone Project - Copilot Instructions

**IMPORTANT:** This file contains project-specific instructions. You MUST also read the workspace-level instructions at `../../.github/copilot-instructions.md` for multi-repo context and critical workflow rules.

---

# ⛔️ STOP: READ THIS BEFORE ANY GIT OPERATION ⛔️

## GIT IRON RULE - NEVER VIOLATE

**BEFORE running `git add`, `git commit`, or `git push`:**

### MANDATORY CHECK:

```
Did user explicitly say one of these trigger phrases?
  ✓ "commit"
  ✓ "commit and push"
  ✓ "c&p" 
  ✓ "push"
  ✓ "save to git"
  ✓ "коммит" (Russian)
  ✓ "запуш" (Russian)
  ✓ "сохрани в git" (Russian)

IF NO → STOP IMMEDIATELY
  1. Show git status
  2. Summarize what's ready
  3. Say: "Ready to commit. Say 'commit and push' when ready."
  4. WAIT - do nothing else

IF YES → Proceed with git operations
```

### WHY THIS IS CRITICAL

- User has forbidden unauthorized commits **multiple times**
- Violating this wastes user's time (manual undo)
- Breaks trust between user and assistant
- **This is not a suggestion - this is an absolute requirement**

### RECENT VIOLATIONS

- **Nov 20, 2025 11:57:** Committed 880a499 without authorization
  - User response: angry, reminded about the rule
  - User demanded: make rule "железным" (iron-clad)

### ENFORCEMENT

Before EVERY git operation, ask yourself:
- **"Did user say 'commit' or equivalent?"**
- If you have ANY doubt → STOP and ask

---

## Project Context

**Name:** AI Code Review Orchestration System  
**Purpose:** Multi-agent system for automated code review using Google ADK  
**Timeline:** Nov 18 → Dec 1, 2025 (13 days)  
**Current:** Day 3, Memory Bank complete (commit 880a499)
**Stack:** Python, Google ADK, Gemini 2.0 Flash Exp, PyGithub  
**Goal:** Kaggle competition - top 3 placement (95-100 points)

## Architecture

Multi-agent system:
- **Repository Merger** - applies PR to create merged state
- **Analyzer Agent** - security (bandit) + complexity (radon) analysis
- **Context Agent** - dependency analysis + impact assessment + **Memory Bank** ✅
- **Reporter Agent** - formats findings, posts to GitHub
- **Orchestrator** - coordinates all agents + shared Memory Bank ✅
- **Memory Bank** - pattern recognition and learning ✅ (NEW)

### File Organization

- NO random files in repository root
- NO CAPSLOCK filenames (STATUS.md, NOTES.md, etc.)
- Use proper directories: `docs/`, `scripts/`, `tests/`, `demos/`
- For agent memory/notes: update THIS file (.github/copilot-instructions.md)
- For user documentation: only when explicitly requested in `docs/`

### Emojis

- NO emojis in code, documentation, or responses
- Exception: demo scripts may have emojis for visual separation

## Project Structure

```
capstone/
├── .github/
│   └── copilot-instructions.md    # This file
├── src/
│   ├── agents/                    # Agent implementations
│   │   ├── analyzer.py            # Security + complexity
│   │   ├── context.py             # Dependencies + impact
│   │   ├── reporter.py            # Report formatting + verdict
│   │   └── orchestrator.py        # Multi-agent coordination
│   ├── tools/                     # Reusable tools
│   │   ├── diff_parser.py
│   │   ├── security_scanner.py
│   │   ├── complexity_analyzer.py
│   │   ├── dependency_analyzer.py
│   │   └── repo_merger.py
│   └── memory/                    # Memory system (planned)
├── tests/
│   ├── fixtures/                  # Test data
│   │   ├── diffs/                 # Pre-generated git diffs
│   │   ├── test-app/              # Sample Flask app
│   │   ├── changesets.py
│   │   └── mock_pr.py
│   └── unit/                      # Unit tests (70 passing)
├── demos/                         # Demo scripts
│   ├── demo_analyzer.py
│   ├── demo_context.py
│   ├── demo_reporter.py
│   └── demo_orchestrator.py
├── scripts/                       # Utility scripts
│   └── generate_demo_diff.py
└── docs/                          # Documentation
    ├── project-plan.md
    └── testing-strategy.md
```

## Testing Standards

- Write unit tests for all new tools
- Use fixtures from `tests/fixtures/`
- Run tests before claiming work is done: `pytest tests/unit/ --ignore=tests/unit/test_changesets.py`
- Current: 70 tests passing (42 core + 10 dependency + 8 reporter + 10 orchestrator)

## Development Status (Day 3 of 13)

**Completed:**
- ✅ Phase 1: Design & Setup (Days 1-2)
- ✅ Repository Merger (pre-processing)
- ✅ Analyzer Agent (security + complexity) - 8 security + 1 complexity issues detected
- ✅ Context Agent (dependencies + impact) - AST-based + AI insights
- ✅ Reporter Agent (formatting + verdict) - GitHub-ready markdown with APPROVE/COMMENT/REQUEST_CHANGES
- ✅ Orchestrator Agent (coordination) - Parallel execution, retry logic, graceful degradation

**Current Phase:**
- Day 3: Completed Orchestrator (significantly ahead of schedule)
- All core agents working end-to-end
- Ready for Memory Bank and GitHub integration

**Next:**
- Days 4-5: Memory Bank (ADK InMemorySessionService for pattern recognition)
- Day 6: GitHub integration (PyGithub for live PR reviews)
- Days 7-8: End-to-end testing with real repos
- Days 9-10: Evaluation framework (LLM-as-judge)
- Days 11-13: Documentation, video, deployment guide

## Key Technologies

- **ADK (Agent Development Kit)** - Google's framework for agents
- **Gemini 2.0 Flash Exp** - LLM for AI insights (temperature=0.3)
- **Vertex AI RAG** - STABLE API ONLY: `from vertexai import rag` (NOT preview!)
- **bandit** - Python security scanner
- **radon** - Python complexity analyzer
- **unidiff** - Git diff parser
- **PyGithub** - GitHub API client

## CRITICAL: Vertex AI API Rules

**ALWAYS use stable API:**
```python
from vertexai import rag  # CORRECT - stable GA API
```

**NEVER use preview API:**
```python
from vertexai.preview import rag  # WRONG - deprecated, forbidden!
```

**Why this matters:**
- We migrated to stable API (GA) on Nov 29, 2025
- Preview API is deprecated and causes confusion
- All RAG operations (corpus, upload, query) use stable API
- No exceptions - this rule applies to ALL files

## Common Patterns

### Creating a new tool:
1. Create in `src/tools/`
2. Write unit tests in `tests/unit/test_<name>.py`
3. Create demo in `demos/demo_<name>.py`
4. Run tests to verify

### Creating a new agent:
1. Create in `src/agents/`
2. Initialize with Gemini client
3. Implement main method (e.g., `analyze_context()`)
4. Add AI insights generation
5. Create demo script

### Working with fixtures:
- Use `tests/fixtures/diffs/` for pre-generated diffs
- Use `tests/fixtures/test-app/` as sample repo
- Generate new diffs: `from scripts.generate_demo_diff import generate_diff`

## ADK Runner Configuration

**CRITICAL:** Always use correct `app_name` in InMemoryRunner to avoid warnings.

```python
# CORRECT - matches ADK agent loading path
runner = InMemoryRunner(agent=my_agent, app_name="agents")

# WRONG - causes "app name mismatch" warning
runner = InMemoryRunner(agent=my_agent, app_name="quality_guardian")
```

**Why:** ADK determines expected app_name from the path where agent is loaded. Since agents import from `google.adk.agents`, ADK expects `app_name="agents"`. Using a different name causes warnings about mismatch.

**Rule:** Always set `app_name="agents"` for all InMemoryRunner instances in this project.

## Test Fixture Quality Patterns

**CRITICAL FOR UNDERSTANDING TESTS AND DEMOS**

Our test fixture repository (`RostislavDublin/quality-guardian-test-fixture`) contains **16 commits with intentional quality patterns**. These are **NOT random** - they simulate realistic development cycles.

**Full Documentation:** `tests/fixtures/QUALITY_PATTERNS.md`

### Quick Reference - Quality Lifecycle

```
Phase 1: IMPROVING (commits 1-5)     → 82.6 to 86.8 (+4.2)
  Initial development, security fixes

Phase 2: REGRESSION (commits 5-7)    → 86.8 to 83.8 (-3.0)
  Removed validation, unsafe features

Phase 3: RECOVERY (commits 7-9)      → 83.8 to ~89 (+5)
  Security fixes BUT eval() remains (blocks full recovery)

Phase 4: PLATEAU (commits 9-11)      → ~89 to ~90 (flat)
  New features added but eval() prevents quality growth
  KEY INSIGHT: Features don't improve quality when vulnerabilities exist

Phase 5: SPIKE UP (commit 12)        → 90 to ~93 (+3)
  Remove eval() → sharp quality improvement

Phase 6: PEAK (commit 13)            → ~93 to ~95 (+2)
  Add authentication on clean codebase

Phase 7: FINAL REGRESSION (14-15)    → 95 to 80.8 (-14)
  Rushed features, disabled logging
```

### Why This Matters

1. **Quality scores are GENERATED** by Guardian agent analyzing real code
2. **Patterns test agent capabilities**: IMPROVING, REGRESSION, RECOVERY, SPIKE, PLATEAU
3. **eval() is intentional**: Demonstrates how critical vulnerabilities block quality improvements
4. **Fixture represents reality**: Technical debt, deadline pressure, remediation efforts

### When Working with Tests/Demos

- **Understand the patterns** before modifying fixture commits
- **Changing commit code** → quality scores change (not hardcoded!)
- **Tests expect patterns** - don't break them accidentally
- **Demos demonstrate detection** - not just reporting numbers

**For auditors:** This fixture proves we understand causal relationships between code changes and quality metrics.

## Remember

1. **NEVER commit without "commit" command from user**
2. NO emojis
3. NO random files in repo root
4. Write tests for everything
5. Use fixtures for consistency
6. Check project-plan.md for current phase
7. Run tests before claiming done
8. **Always use `app_name="agents"` in InMemoryRunner**
9. **Read `tests/fixtures/QUALITY_PATTERNS.md` before changing fixtures**
