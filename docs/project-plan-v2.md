# AI Code Review System v2 - Project Plan

**Project Name:** GitHub-First PR Review System  
**Tagline:** "Interactive Code Review Bot that Learns Your Team's Standards"  
**Track:** Enterprise Agents  
**Target Score:** 95-100 points  
**Timeline:** Nov 20 → Dec 1, 2025 (11 days remaining)

---

## 🎯 Strategic Positioning

### What Changed from v1:
**v1 (abandoned):** Generic diff analysis + over-engineered Memory Bank  
**v2 (this):** Deep GitHub integration + learning from PR feedback

### Market Context (Nov 2025):
- **GitHub Copilot** generates code at AI speed → bottleneck is review
- **PR-based workflow** is industry standard (986M code pushes on GitHub)
- **Team standards vary** - generic linters create noise, not value
- **Interactive learning** - bots should adapt, not just report

### Our Unique Value:
"Code review bot that posts inline comments on PR like a human, learns your team's standards from your feedback, and stops nagging about things you don't care about."

### Key Differentiators:
1. **Inline Comments** - Not a single report, but contextual threads on each line
2. **Interactive Learning** - Analyzes developer responses, builds team standards
3. **Incremental Reviews** - Tracks PR progress: "Fixed 3, 2 remain"
4. **GitHub-Native** - Uses PR as storage, not duplicating data

---

## 🏗️ Architecture Overview

### Core Principle: GitHub = Our Database

```
┌─────────────────────────────────────────┐
│         GitHub (Storage & UI)           │
│  ┌─────────────────────────────────┐   │
│  │  PR Entity (First-Class Citizen) │   │
│  │  ├─ Commits (history)            │   │
│  │  ├─ Review Comments (threads)    │   │
│  │  ├─ Files Changed (diff)         │   │
│  │  └─ Metadata (author, labels)    │   │
│  └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │ Webhook
┌─────────────────▼───────────────────────┐
│     GitHub Integration Layer            │
│  - Webhook handler                      │
│  - PR context loader                    │
│  - Comment formatter/poster             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Core Analysis Agents              │
│  - Analyzer: security, complexity       │
│  - Context: dependencies, impact        │
│  - Learner: extract standards from      │
│              developer feedback         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│    Memory Bank (Minimal)                │
│  - Team standards ONLY                  │
│  - Evidence: links to PR threads        │
│  - No raw data duplication              │
└─────────────────────────────────────────┘
```

### System Components:

**1. GitHub Integration Layer**
- **Webhook Handler:** Receive PR events (opened, synchronize, comment)
- **PR Context Loader:** 
  - Load PR diff, files, commits
  - Load previous reviews from THIS PR
  - Load open/resolved threads
- **Comment Manager:**
  - Create inline review comments (specific line)
  - Reply in threads
  - Resolve threads when fixed

**2. Core Agents**

**Analyzer Agent:**
- Role: Find issues in code
- Input: Diff + file content
- Tools: Bandit (security), Radon (complexity), custom rules
- Output: List of issues with location (file, line)

**Context Agent:**
- Role: Understand broader impact
- Input: Changed files + full repo
- Tools: AST parser, dependency analyzer
- Output: Affected modules, integration risks

**Learner Agent:**
- Role: Extract team standards from feedback
- Input: Developer responses in PR threads
- Tools: LLM to parse intent, pattern detection
- Output: Team standards (when sufficient evidence)

**3. Memory Bank (Minimal - Vertex AI RAG)**

**Technology:** Vertex AI RAG Engine (Corpus + File API)

**Stores ONLY:**
```python
# Document in RAG Corpus
{
  "standard_id": "uuid",
  "rule": "PascalCase acceptable for API handlers",
  "category": "naming",
  "scope": "api/handlers/*.py",
  "evidence": [
    {"pr": 123, "thread_id": "comment_456", "developer": "@alice"},
    {"pr": 145, "thread_id": "comment_789", "developer": "@bob"}
  ],
  "confidence": 0.85,  # based on evidence count
  "override": {"naming-convention": "info"}  # downgrade severity
}
```

**Storage:**
- ✅ Vertex AI RAG Corpus (permanent, semantic search)
- ✅ Service Account auth (no API keys)
- ✅ Metadata filters (category, confidence, scope)

**Does NOT store:**
- PR history (GitHub has it)
- Review comments (GitHub has it)
- Diff content (GitHub has it)

---

## 🔄 Workflows

### Workflow 1: First Review (PR Opened)

```
1. Webhook: pull_request.opened
   └─ payload: pr_number, repo, base_sha, head_sha

2. Load Context:
   ├─ Get PR diff from GitHub
   ├─ Check: First review? (no previous bot comments)
   └─ Load team standards from Memory Bank

3. Analyze:
   ├─ Analyzer: Run security + complexity scans
   ├─ Context: Check dependencies, integration
   └─ Filter issues using team standards

4. Post Review:
   ├─ For each issue:
   │   └─ Create inline comment on specific line
   └─ Create review summary comment

Result: PR has 10 inline threads + 1 summary
```

### Workflow 2: Incremental Review (New Commit)

```
1. Webhook: pull_request.synchronize
   └─ new commit pushed to PR

2. Load Incremental Context:
   ├─ Get previous bot review
   ├─ Load open threads (not fixed yet)
   ├─ Load resolved threads (what was fixed)
   └─ Get new commits since last review

3. Analyze Changes:
   ├─ Run analysis on NEW code only
   └─ Check if open issues still present

4. Update Review:
   ├─ Resolved issues: Add comment "✅ Fixed in commit abc"
   ├─ Still open: Update if code changed
   └─ New issues: Create new threads

Result: Progress tracked, no duplicate comments
```

### Workflow 3: Learning from Feedback

```
1. Webhook: pull_request_review_comment.created
   └─ developer replied in thread

2. Analyze Response:
   ├─ LLM parses developer intent:
   │   ├─ "Fixed" → acknowledge
   │   ├─ "This is our standard" → potential learning
   │   └─ "False positive" → adjust confidence
   └─ Store feedback in evidence buffer

3. Check Pattern:
   ├─ Query: Similar feedback across PRs?
   └─ If 3+ developers say same thing:
       └─ Extract team standard

4. Create Standard:
   ├─ Store in Memory Bank with evidence
   ├─ Reply in thread: "✅ Understood, added to team standards"
   └─ Resolve thread

Result: Bot learns, stops nagging about team conventions
```

---

## 📋 Course Concepts Coverage (6 concepts)

### Required: 3 | Delivering: 6

1. ✅ **Multi-Agent System**
   - Analyzer + Context + Learner agents
   - Orchestrated by Integration Layer

2. ✅ **Custom Tools**
   - GitHub API integration (webhooks, comments, threads)
   - Static analyzers (Bandit, Radon)
   - Diff parser

3. ✅ **Memory System**
   - Minimal Memory Bank for team standards
   - Learning from PR thread feedback
   - Evidence-based confidence scoring

4. ✅ **Evaluation Framework**
   - LLM-as-judge for review quality
   - Acceptance rate tracking
   - False positive metrics

5. ✅ **Observability**
   - ADK logging for each agent
   - Webhook event tracking
   - Learning event tracing

6. ✅ **Production Deployment**
   - Vertex AI Agent Engine
   - Cloud Run for webhook handler
   - Service Account auth

---

## 🛠️ Technical Stack

### Core:
- **Framework:** Google ADK (Python 3.12)
- **LLM:** Gemini 2.5 Flash via **Vertex AI only** (no dual-mode complexity)
- **Memory:** Vertex AI RAG Engine (for team standards)
- **GitHub:** PyGithub (API client)
- **Tools:** Bandit, Radon, GitPython

### Deployment:
- **Platform:** Vertex AI only (development & production)
- **Runtime:** Vertex AI Agent Engine
- **Webhook:** Cloud Run (receive GitHub events)
- **Auth:** Service Account (no API keys)
- **Secrets:** Secret Manager (GitHub token)

### Why Vertex AI Only:
- ❌ **No dual-mode** (Google AI Studio vs Vertex AI)
- ❌ **No free tier limitations** (quota issues, feature gaps)
- ✅ **Single codebase** (no environment switching)
- ✅ **Production-ready from day 1** (same env for dev & prod)
- ✅ **Cost acceptable** (few dollars for competition worth it)

### Testing:
- **Unit:** pytest with mocks
- **Integration:** Real GitHub API (test repo)
- **E2E:** Trigger webhook → verify comments

---

## 📦 What We Reuse from v1

### Copy As-Is (Stable):

```
capstone/                       capstone2/
├── tools/                  →   ├── tools/
│   ├── diff_parser.py          │   ├── diff_parser.py
│   ├── security_scanner.py     │   ├── security_scanner.py
│   ├── complexity_analyzer.py  │   ├── complexity_analyzer.py
│   └── repo_merger.py          │   └── repo_merger.py
├── tests/fixtures/         →   ├── tests/fixtures/
│   ├── test-app/               │   ├── test-app/
│   └── diffs/                  │   └── diffs/
├── pyproject.toml          →   ├── pyproject.toml (adapted)
├── requirements/           →   ├── requirements/
└── docs/                   →   └── docs/
    ├── capstone-requirements   │   ├── capstone-requirements
    └── market-trends-2025      │   └── market-trends-2025
```

### Redesign (New Architecture):

- ❌ `src/agents/*` → NEW: GitHub-aware agents
- ❌ `src/models.py` → NEW: PR-centric models
- ❌ `src/memory/*` → NEW: Minimal Memory Bank
- ❌ `src/github/` → NEW: Integration layer
- ❌ Tests → NEW: GitHub API mocks

---

## 🎬 Demo Strategy (3 PRs)

### Test Repository Setup:
```
Create: RostislavDublin/review-bot-demo
- Simple Python app
- 3 PRs pre-created with different scenarios
```

### PR #1: "Generic Bot Behavior"
```
Code: PEP8 violations, but intentional (team uses own style)

Bot Initial Review:
├─ 15 issues flagged (all style/naming)
└─ Generic PEP8 enforcement

Developer Response:
├─ Thread 1: "We use PascalCase for handlers, not snake_case"
├─ Thread 2: "120 char limit, not 80"
└─ Thread 3: "We allow wildcard imports in __init__.py"

Result: Bot stores feedback, doesn't learn yet (need more evidence)
```

### PR #2: "Building Evidence"
```
Code: Similar style "violations"

Bot Review:
├─ Flags same issues again
└─ But notes: "Similar feedback in PR#1"

Developer Response:
├─ @alice: "Already told you, PascalCase is fine"
├─ @bob: "Yeah, we always use PascalCase for handlers"

Bot Learns:
├─ 3 developers confirmed pattern
├─ Creates team standard
└─ Replies: "✅ Got it! Added to team standards"

Result: Standard created with evidence from 2 PRs
```

### PR #3: "Adapted Behavior"
```
Code: Same style + 2 real security issues

Bot Review:
├─ ℹ️ "PascalCase detected (matches team standard)"
├─ ℹ️ "Line 95 chars (team allows 120)"
├─ ❌ "SQL injection on line 42"
└─ ❌ "Hardcoded secret on line 67"

Developer:
├─ Fixes 2 security issues
└─ No noise about style

Result: Bot provides value, respects team context
```

---

## 📊 Evaluation Metrics

### Quality Metrics:
1. **Precision:** % of flagged issues that are real problems
2. **Recall:** % of real problems that were flagged
3. **Acceptance Rate:** % of suggestions that developers implement
4. **False Positive Rate:** % of flagged issues marked as "not an issue"

### Learning Metrics:
1. **Standards Learned:** Count of team standards extracted
2. **Learning Speed:** PRs needed to learn a standard (target: 2-3)
3. **Confidence Accuracy:** Do high-confidence standards get accepted?

### User Experience:
1. **Review Latency:** Time from commit to bot comment (target: <2 min)
2. **Noise Reduction:** % decrease in irrelevant issues (PR1 vs PR3)
3. **Thread Engagement:** % of bot comments that get developer replies

---

## 📅 Implementation Timeline (11 days)

### Days 3-4 (Nov 20-21): Foundation
- [x] Architecture design
- [x] Clean v2 branch
- [ ] GitHub integration layer (webhooks, API client)
- [ ] Basic PR context loader

### Days 5-6 (Nov 22-23): Core Agents
- [ ] Analyzer agent (reuse tools from v1)
- [ ] Context agent (dependency analysis)
- [ ] Inline comment formatter

### Days 7-8 (Nov 24-25): Learning System
- [ ] Learner agent (parse feedback)
- [ ] Minimal Memory Bank (team standards)
- [ ] Evidence collection & pattern detection

### Days 9-10 (Nov 26-27): Integration & Testing
- [ ] E2E workflow (webhook → review → feedback → learn)
- [ ] Test repo with 3 PRs
- [ ] Integration tests with GitHub API

### Days 11-12 (Nov 28-29): Deployment & Evaluation
- [ ] Deploy to Vertex AI
- [ ] Evaluation framework (LLM-as-judge)
- [ ] Metrics collection

### Day 13 (Nov 30): Documentation & Submission
- [ ] README with demo
- [ ] Video recording (3 min)
- [ ] Submit to Kaggle

---

## 🚧 Risks & Mitigation

### Risk 1: GitHub API Rate Limits
- **Mitigation:** Use authenticated requests (5000/hour)
- **Fallback:** Cache PR data locally during testing

### Risk 2: Learning Takes Too Long
- **Mitigation:** Lower threshold to 2 confirmations (not 3)
- **Fallback:** Pre-seed 1-2 standards for demo

### Risk 3: Webhook Latency
- **Mitigation:** Use Cloud Run (fast cold start)
- **Fallback:** Async processing, acknowledge webhook immediately

### Risk 4: Inline Comments Complexity
- **Mitigation:** Start with simple format, iterate
- **Fallback:** Use review-level comments if inline fails

---

## ✅ Success Criteria

### Minimum (Pass):
- ✅ Demonstrates 3+ course concepts
- ✅ Working webhook integration
- ✅ Posts review comments on PR
- ✅ Clear documentation

### Target (95-100 points):
- ✅ 6 course concepts demonstrated
- ✅ Interactive learning from feedback
- ✅ 3-PR demo showing evolution
- ✅ Production deployment working
- ✅ Evaluation framework with metrics
- ✅ Professional documentation + video

---

**Last Updated:** Nov 20, 2025  
**Status:** Day 3 - Architecture complete, starting implementation  
**Branch:** v2-github-first
