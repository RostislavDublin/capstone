# Capstone Project - Copilot Instructions

**IMPORTANT:** This file contains project-specific instructions. You MUST also read the workspace-level instructions at `../../.github/copilot-instructions.md` for multi-repo context and critical workflow rules.

## Project Context

**Name:** AI Code Review Orchestration System  
**Purpose:** Multi-agent system for automated code review using Google ADK  
**Timeline:** Nov 18 → Dec 1, 2025 (13 days)  
**Stack:** Python, Google ADK, Gemini 2.0 Flash Exp, PyGithub  
**Goal:** Kaggle competition - top 3 placement (95-100 points)

## Architecture

Multi-agent system:
- **Repository Merger** - applies PR to create merged state
- **Analyzer Agent** - security (bandit) + complexity (radon) analysis
- **Context Agent** - dependency analysis + impact assessment
- **Reporter Agent** - formats findings, posts to GitHub
- **Orchestrator** - coordinates all agents

## Critical Rules

### Git Workflow - ABSOLUTE REQUIREMENT

**NEVER commit or push without explicit user permission.**

User must explicitly say one of:
- "commit"
- "commit and push"
- "save to git"
- "push to github"

**FORBIDDEN actions without permission:**
- `git add`
- `git commit`
- `git push`
- Any git operation that changes repository state

**Correct workflow:**
1. Complete all work
2. Show `git status` or list changes
3. **WAIT for user to say "commit"**
4. Only then: add, commit, push

**Violation consequences:**
User has to manually undo commits. This wastes time and breaks trust.

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
- **bandit** - Python security scanner
- **radon** - Python complexity analyzer
- **unidiff** - Git diff parser
- **PyGithub** - GitHub API client

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

## Remember

1. **NEVER commit without "commit" command from user**
2. NO emojis
3. NO random files in repo root
4. Write tests for everything
5. Use fixtures for consistency
6. Check project-plan.md for current phase
7. Run tests before claiming done
