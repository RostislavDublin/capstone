# Demo Scripts

Interactive demonstration scripts for testing and showcasing the AI Code Review Orchestration System.

## 📋 Overview

Demos are **manual testing and demonstration scripts** that:
- Show the system in action with real data
- Help with debugging and development
- Use real APIs (Gemini, GitHub, Vertex AI, Firestore, RAG)
- **Are NOT automated tests** (use `tests/` for that)

---

## ⭐ Main Demo (Start Here)

### `demo_quality_guardian_agent.py` - **RECOMMENDED**
**Complete ADK Multi-Agent Workflow - Production-Ready**

This is the **most comprehensive demo** that shows the entire system working end-to-end.

**What it demonstrates:**
- ✅ Full ADK Agent pattern (deployment-ready architecture)
- ✅ Natural language commands → Agent → Tool execution
- ✅ Complete workflow: Bootstrap → Sync → Query
- ✅ Dual storage: Firestore (structured) + RAG Corpus (semantic)
- ✅ GitHub integration (real commits)
- ✅ 4 modes: automated tests, architecture view, interactive chat, all

**Side effects:**
- **Populates test database** with fixture data (14-16 commits)
- Clears existing Firestore and RAG data before running
- Creates real GitHub commits in test repository

**Usage:**
```bash
python demos/demo_quality_guardian_agent.py
```

**Modes:**
- `1` - Natural Language Commands (full automated demo)
- `2` - Agent Composition (show architecture)
- `3` - Interactive Mode (chat with agent)
- `4` - Run All

**Requirements:**
- `GITHUB_TOKEN` in `.env`
- `GOOGLE_CLOUD_PROJECT` in `.env`
- Test repo: `TEST_REPO_NAME` (default: `quality-guardian-test-fixture`)

**Perfect for:**
- First-time users exploring the system
- Demos and presentations
- Validating end-to-end functionality
- Preparing test data for other demos

---

## 🎯 Specialized Agent Demos

These demos test **specific agents** in isolation (faster iteration during development).

### `demo_trends_agent.py`
**Trends Analysis Agent - Quick Testing**

Tests `trends_agent` functionality in isolation without bootstrap/sync overhead.

**Prerequisites:** Run `demo_quality_guardian_agent.py` first to populate data.

**What it tests:**
- Quality score trends over time
- Security/complexity issue trends
- File-specific analysis
- Commit statistics

**Usage:**
```bash
python demos/demo_trends_agent.py
```

---

### `demo_root_cause.py`
**Root Cause Analysis - RAG Semantic Search**

Demonstrates the **killer feature**: finding WHY quality degraded using RAG.

**Prerequisites:** Run `demo_quality_guardian_agent.py` first to populate RAG.

**What it demonstrates:**
- Semantic search through commit history
- Pattern recognition across files
- Timeline reconstruction
- Evidence gathering (commits, files, lines)

**Usage:**
```bash
python demos/demo_root_cause.py
```

**Example output:**
```
Root Causes:
1. SQL injection in app/database.py (string-based queries)
2. High complexity in app/utils.py (process_data function)

Timeline:
- 2025-11-01: Hardcoded passwords introduced
- 2025-11-05: Passwords fixed, but complexity remained
```

---

### `demo_orchestrator.py`
**Query Orchestrator - Routing Logic**

Tests orchestrator's ability to route queries to correct sub-agents.

**Prerequisites:** Run `demo_quality_guardian_agent.py` first.

**What it tests:**
1. Simple trends query → routes to `trends_agent` only
2. Simple root cause → routes to `root_cause_agent` only  
3. Composite query → routes to BOTH and merges results

**Usage:**
```bash
python demos/demo_orchestrator.py
```

**Perfect for:** Verifying orchestrator routing logic without full hierarchy overhead.

---

### `demo_quality_guardian.py`
**Full 4-Level Hierarchy Test**

Tests complete agent hierarchy: Guardian → Orchestrator → Sub-agents → Tools

**Prerequisites:** Run `demo_quality_guardian_agent.py` first.

**What it verifies:**
- Information flows correctly through 4 levels
- No response distortion or data loss
- Same results as `demo_orchestrator.py` but through full hierarchy

**Usage:**
```bash
python demos/demo_quality_guardian.py
```

**Difference from `demo_quality_guardian_agent.py`:**
- `_agent.py` = Full workflow (bootstrap, sync, query) + data setup
- `.py` = Query-only hierarchy test (assumes data exists)

---

## 🔧 Feature-Specific Demos

### `demo_composite_queries.py`
**Composite Query Handling**

Shows how orchestrator combines multiple agents for complex questions.

**Example:**
```
Query: "Show trends AND explain quality drops"
→ Calls trends_agent + root_cause_agent
→ Merges results into unified response
```

**Usage:**
```bash
python demos/demo_composite_queries.py
```

---

### `demo_trends_filtering.py`
**Advanced Filtering in Trends**

Tests advanced filtering capabilities:
- File-specific trends: `app/database.py` issues only
- Author-specific: commits by specific developer
- Quality thresholds: only low-quality commits
- Combined filters

**Prerequisites:** Run `demo_quality_guardian_agent.py` first.

**Usage:**
```bash
python demos/demo_trends_filtering.py
```

---

### `demo_phased_commits.py`
**Bootstrap + Sync Workflow**

Demonstrates the phased commit application pattern:
1. Reset repo to 3 commits (bootstrap phase)
2. Add 2 more commits (sync phase)

**Usage:**
```bash
python demos/demo_phased_commits.py
```

**Perfect for:** Testing incremental analysis and sync logic.

---

## 🗂️ Demo Execution Order

**If you're new, follow this order:**

1. **Start:** `demo_quality_guardian_agent.py` (mode 1)
   - Sets up test data
   - Shows full workflow

2. **Explore agents:**
   - `demo_trends_agent.py` - Quality trends
   - `demo_root_cause.py` - Why quality dropped

3. **Test routing:**
   - `demo_orchestrator.py` - Agent coordination
   - `demo_quality_guardian.py` - Full hierarchy

4. **Advanced features:**
   - `demo_composite_queries.py` - Complex questions
   - `demo_trends_filtering.py` - Filtered analysis

---

## 📝 Requirements

**All demos need:**
```bash
# .env file with:
GITHUB_TOKEN=ghp_xxx...
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_LOCATION=us-west1
TEST_REPO_NAME=your-test-repo
FIRESTORE_DATABASE=(default)
FIRESTORE_COLLECTION_PREFIX=quality-guardian
```

**Python environment:**
```bash
cd capstone
source .venv/bin/activate  # or your venv
```

---

## 🎨 Adding New Demo

1. Create `demo_*.py` in this folder
2. Add docstring describing purpose
3. Use template:

```python
"""Demo: [Feature Name] - [Brief Description].

[Detailed explanation of what this demonstrates]
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from your_module import YourClass


def main():
    """Run the demo."""
    print("🚀 Starting demo...")
    # Your demo code
    

if __name__ == "__main__":
    main()
```

4. Document in this README under appropriate section
5. Mention any prerequisites or side effects

---

## ⚠️ Important Notes

- **Side Effects:** `demo_quality_guardian_agent.py` populates test database
- **Prerequisites:** Most demos need data from main demo first
- **Not CI/CD:** Demos are NOT run in continuous integration
- **Real APIs:** Uses real Gemini, GitHub, Firestore, RAG services
- **No Secrets:** Never commit API keys or tokens

---

## 📚 See Also

- `tests/` - Automated test suite (pytest)
- `deployment/` - Deployment scripts and configuration
- `docs/` - Architecture and technical documentation
