# Demo Scripts

Interactive demonstration scripts for manual testing and validation of the AI Code Review system.

## What's Here

This folder contains scripts for **manual testing and demonstration** that:
- Show the system in action
- Help with debugging and development
- Use real APIs (Gemini, GitHub, Vertex AI)
- **Are NOT automated tests** (use `tests/` for that)

## 🟢 Working Demos

### 1. `demo_quality_guardian_agent.py` ⭐ **MAIN**
**ADK Multi-Agent Implementation - Production-Ready Architecture**

Demonstrates full Quality Guardian Agent workflow using Google ADK:
- Natural language commands → ADK Agent → Tool execution
- RAG Corpus integration (Vertex AI) for persistent storage
- Bootstrap → Sync → Query workflow
- GitHub API integration (real repository commits)

**Usage:**
```bash
cd /Users/Rostislav_Dublin/src/drs/ai/capstone
python demos/demo_quality_guardian_agent.py 1
```

**Modes:**
- Mode 1: Interactive menu (all 4 tests sequentially)
- Mode 2: Bootstrap only (analyze N commits)
- Mode 3: Sync only (check for new commits)
- Mode 4: Query only (ask questions about audits)

**Requirements:**
- GitHub token: `GITHUB_TOKEN` in `.env.dev`
- Google Cloud project: `GOOGLE_CLOUD_PROJECT`
- Test repository: `RostislavDublin/capstone-test-fixture`

**Example output:**
```
✅ Loaded environment from .env.dev

╔════════════════════════════════════════════════════════════════════╗
║  Quality Guardian Agent Demo - ADK Implementation (Google Agent)   ║
╚════════════════════════════════════════════════════════════════════╝

TEST 1: Bootstrap with 5 commits
✓ Bootstrap agent completed analysis of 5 commits

TEST 2: Sync (check for new commits)
✓ Found 2 new commits, analysis complete

TEST 3: Query RAG
Question: What security issues were found?
✓ Query results: Found 3 SQL injection patterns...

TEST 4: Agent Capabilities
✓ Agent can handle: bootstrap, sync, query operations
```

---

### 2. `demo_memory.py`
**Memory Bank - Pattern Learning and Recognition**

Demonstrates how Memory Bank:
- Stores review patterns from code reviews
- Tracks frequency and acceptance rate of patterns
- Stores team coding standards
- Recalls similar patterns during reviews
- Provides statistics on learned patterns

**Usage:**
```bash
cd /Users/Rostislav_Dublin/src/drs/ai/capstone
python demos/demo_memory.py
```

**Requirements:**
- No external dependencies (uses in-memory storage)

**What's demonstrated:**
```
================================================================================
                     SCENARIO 1: Learning from Code Reviews                     
================================================================================

Review 1: Found SQL injection in PR #123
   ✓ Pattern stored: f0e5584598cce1ac
   ✓ Developer fixed the issue (accepted)

Review 2: Found similar SQL injection in PR #156
   ✓ Same pattern detected: True
   ✓ Frequency increased to 2

SCENARIO 2: Team Standards
   ✓ Stored: Always use type hints in function signatures
   ✓ Stored: Max line length is 88 characters (Black)

SCENARIO 3: Pattern Statistics
   Most common patterns:
   1. SQL injection: 3 occurrences (100% accepted)
   2. Missing error handling: 2 occurrences (50% accepted)
```

---

## How to Add New Demo

1. Create script `demo_*.py` in this folder
2. Add docstring with description and usage example
3. Add section to this README
4. Use `sys.path.insert(0, str(Path(__file__).parent.parent / "src"))` for imports

**Template:**
```python
"""Demo script for [feature name].

Demonstrates [what it does].
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

## Important Notes

- **Do NOT commit API keys** in scripts
- Demos **are NOT run** in CI/CD
- For automated testing use `tests/`
- Demos may **require external services** (Gemini API, GitHub API)

## See Also

- `tests/` - automated tests (pytest)
- `scripts/` - development and deployment utilities
- `docs/testing-strategy.md` - testing strategy
