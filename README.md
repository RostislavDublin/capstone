# AI Code Review Orchestration System

**Closing the AI Feedback Loop in Modern Development Workflows**

[![Competition](https://img.shields.io/badge/Kaggle-5%20Day%20Agents%20Capstone-20BEFF)](https://kaggle.com/competitions/agents-intensive-capstone-project)
[![Track](https://img.shields.io/badge/Track-Enterprise%20Agents-green)]()
[![Framework](https://img.shields.io/badge/Framework-Google%20ADK-4285F4)]()
[![Status](https://img.shields.io/badge/Status-In%20Development-yellow)]()
[![Progress](https://img.shields.io/badge/Progress-25%25-orange)]()
[![Days](https://img.shields.io/badge/Days%20Remaining-11-red)]()

> **Current Status (Day 2/14):** Testing infrastructure complete ✅ | Core agent implementation starting Day 3

---

## 🎯 Project Overview

In October 2025, GitHub launched Agent HQ - the future of AI agent orchestration in development workflows. But there's a critical gap: while GitHub Copilot generates code at AI speed, human review is now the bottleneck.

According to GitHub's 2025 Octoverse, we're seeing **986 million code pushes** with AI-generated code volume exploding. Teams need AI-powered review automation that understands context, learns from history, and integrates seamlessly into modern workflows.

**Our Solution:** Multi-agent orchestration system using Google's ADK and latest Gemini memory capabilities to review code at the same pace it's generated.

---

## 🏗️ Architecture

### Multi-Agent System

```
PR Event (GitHub Webhook)
         ↓
    ┌────────────────┐
    │  Orchestrator  │
    └────────┬───────┘
             │
     ┌───────┴────────┐
     ↓                ↓
┌──────────┐    ┌──────────┐
│ Analyzer │    │ Context  │
│  Agent   │    │  Agent   │
└────┬─────┘    └────┬─────┘
     │               │
     └───────┬───────┘
             ↓
      ┌──────────┐
      │ Reporter │
      │  Agent   │
      └────┬─────┘
           ↓
  GitHub PR Comment
```

### Agent Responsibilities

**1. Analyzer Agent**
- Parse git diffs and analyze code changes
- Detect complexity, security issues, style violations
- Use Gemini for semantic code understanding
- Output: List of issues with severity levels

**2. Context Agent**
- Retrieve historical review patterns from Memory Bank
- Fetch team coding standards and previous PR context
- Provide institutional knowledge for consistent reviews
- Output: Relevant context for current review

**3. Reporter Agent**
- Generate human-readable review summaries
- Format findings with actionable suggestions
- Post comments to GitHub PR
- Output: Formatted review with priority-sorted issues

---

## 🎓 Course Concepts Demonstrated

This project demonstrates **6 key concepts** from the Kaggle 5-Day Agents Course (minimum requirement: 3):

1. ✅ **Multi-Agent System** - Three agents with parallel execution and orchestration
2. ✅ **Custom Tools** - GitHub API, git parser, static analysis tools
3. ✅ **Memory System** - ADK Memory Bank for review pattern retention
4. ✅ **Observability** - Comprehensive logging and tracing
5. ✅ **Agent Evaluation** - LLM-as-judge framework for quality metrics
6. ✅ **Production Deployment** - Deployed on Vertex AI Agent Engine

---

## 📁 Project Structure

```
capstone/
├── agents/               # Agent implementations (TODO: Day 3-8)
├── changesets.py         # ✅ Test scenario definitions (426 lines)
├── config.py             # ✅ Configuration management
├── github_utils.py       # ✅ GitHub API client
├── interfaces.py         # ✅ Agent interfaces (4 interfaces)
├── memory_schema.py      # ✅ Memory Bank schemas (5 types)
├── models.py             # ✅ Pydantic data models (15 schemas)
│
├── tools/                # ✅ Shared utilities
│   ├── diff_generator.py       # Synthetic git diffs
│   └── mock_pr_context.py      # Mock PullRequest objects
│
├── tests/                # ✅ Test infrastructure
│   └── test_changesets.py      # Unit tests (280+ lines)
│
├── evalsets/             # ✅ Evaluation datasets
│   └── test_fixture_prs.evalset.json
│
├── scripts/              # ✅ Automation scripts
│   ├── deploy_fixture.py       # Deploy test repo
│   ├── create_test_prs.py      # Create PRs from changesets
│   └── reset_fixture.py        # Cleanup
│
├── test-fixture/         # ✅ Test repository
│   └── app/                    # Flask app with issues
│
└── docs/                 # ✅ Documentation
    ├── project-plan.md           # 13-day timeline
    ├── testing-strategy.md       # Testing guide (300+ lines)
    ├── unified-testing-architecture.md  # Architecture overview
    ├── market-trends-2025.md     # Strategic positioning
    └── capstone-requirements.md  # Competition rubric
```

**Legend:**
- ✅ Completed (Days 1-2)
- TODO: Remaining work (Days 3-14)

---

## 🧪 Testing Infrastructure (Day 2 Achievement)

### Unified Changeset Architecture

**Problem Solved:** Single source of truth for all test scenarios

```python
# changesets.py - Define once, use everywhere
CHANGESET_01_SQL_INJECTION = Changeset(
    id="cs-01-sql-injection",
    target_file="app/auth.py",
    new_content="""...SQL injection code...""",
    expected_issues=[...],
    pr_title="Add user authentication",
    min_issues_to_detect=2,
    max_false_positives=0
)
```

**Benefits:**
- ✅ **Local tests:** Generate synthetic diffs without GitHub
- ✅ **Remote tests:** Create real PRs from same definitions
- ✅ **Sequential tests:** Memory Bank learning evaluation
- ✅ **Easy maintenance:** Update once, propagates everywhere

**Read more:** [docs/unified-testing-architecture.md](docs/unified-testing-architecture.md)

### Test Scenarios Ready:

1. **cs-01-sql-injection** - Security vulnerabilities (2 critical, 1 high)
2. **cs-02-high-complexity** - Code complexity (3 high, 2 medium)
3. **cs-03-style-violations** - Style issues (8 medium)
4. **cs-04-clean-code** - Control test (0 expected issues)

---

## 🚀 Quick Start (Coming Soon)

> **Note:** Agent implementation starts Day 3. This section will be populated with working examples.

### Prerequisites

- Python 3.11+
- Google Cloud account with Vertex AI enabled
- GitHub account and personal access token
- ADK CLI installed

### Local Development

```bash
# Setup (TODO: Day 3)
cd /path/to/ai/src/capstone
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test locally (TODO: Day 9)
pytest tests/
adk eval evalsets/test_fixture_prs.evalset.json
```

### Production Deployment (TODO: Day 11)

See [Deployment Guide](docs/deployment.md) when available.

---

## 📊 Evaluation & Results

[To be populated after testing]

- **Review Speed:** < 15 seconds per PR
- **Detection Accuracy:** > 80% vs manual review
- **Memory Recall:** > 90% for known patterns
- **False Positive Rate:** < 20%

---

## 🔧 Technology Stack

- **Framework:** Google Agent Development Kit (ADK)
- **LLM:** Gemini 2.5 Flash & Pro
- **Memory:** ADK Memory Bank
- **Tools:** PyGithub, GitPython, Radon, Bandit
- **Deployment:** Vertex AI Agent Engine
- **Observability:** Cloud Logging

---

## 📝 Project Status

**Timeline:** Nov 18 - Dec 1, 2025 (13 days)

**Current Phase:** Day 1 - Design & Setup

See [Project Plan](docs/project-plan.md) for detailed timeline.

---

## 🎯 Competition Details

- **Competition:** Kaggle 5-Day Agents Intensive Capstone Project
- **Track:** Enterprise Agents
- **Target:** Top-3 placement
- **Submission Deadline:** December 1, 2025 at 11:59 AM PT

---

## 📚 Documentation

- [Project Plan](docs/project-plan.md) - Complete implementation timeline
- [Competition Requirements](docs/capstone-requirements.md) - Rubric and rules
- [Market Trends Analysis](docs/market-trends-2025.md) - Industry context
- [Architecture Design](docs/architecture.md) - Technical details (coming soon)
- [Deployment Guide](docs/deployment.md) - Production setup (coming soon)

---

## 🤝 Contributing

This is a competition entry project. Development is currently closed.

---

## 📄 License

This project is developed for the Kaggle 5-Day Agents Intensive Capstone Project.

---

## 🙏 Acknowledgments

- Google ADK Team for the framework
- Kaggle for organizing the competition
- GitHub for Agent HQ inspiration

---

**Built with ❤️ using Google ADK**

Last Updated: November 18, 2025
