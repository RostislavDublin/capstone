# Quality Guardian - Project Plan v3

**Project Name:** Repository Quality Guardian  
**Tagline:** "Independent Quality Auditor for Engineering Teams"  
**Track:** Enterprise Agents  
**Target Score:** 95-100 points  
**Timeline:** Nov 21 → Dec 1, 2025 (10 days remaining)  
**Current Progress:** Day 3/10 - Backend tools verified (~15% complete)

---

## 🎯 New Concept: From PR Reviewer to Quality Guardian

### The Pivot

**OLD CONCEPT (Abandoned):**
- PR-based code review automation
- Inline comments on pull requests
- **Problem:** GitHub Copilot already does this

**NEW CONCEPT (Quality Guardian):**
- **Independent quality auditor** for release branches
- Monitors every commit to main/release branches
- Stores audit history in RAG (Vertex AI)
- Provides trend analysis and insights on-demand
- **Target audience:** Engineering leads, PMs, Team Leads (not developers)

### Why This Wins

✅ **Doesn't compete with Copilot** - different niche entirely  
✅ **Independent arbitrator** - unaffected by team politics or relaxed standards  
✅ **Long-term memory** - RAG with full audit history  
✅ **Trend analysis** - "How has quality changed over 3 months?"  
✅ **Management tool** - for leads, not for PR discussions  
✅ **Reuses 80% of capstone v1 code** - Memory Bank, analyzers, orchestrator

---

## 🏗️ Architecture: Conversational Agent (No Webhooks)

**Key Decision:** User-initiated audits via natural language commands

### Single Conversational Agent with Three Commands

```
User: Natural Language Command
    ↓
┌──────────────────────────────────┐
│  Quality Guardian Agent          │
│  (Vertex AI Agent Engine)        │
│                                  │
│  Capabilities:                   │
│  - Parse user intent             │
│  - Execute bootstrap/sync/query  │
│  - Coordinate sub-agents         │
│  - Generate responses            │
└──────────┬───────────────────────┘
           │
     ┌─────┴──────┬──────────┐
     ↓            ↓          ↓
┌──────────┐ ┌─────────┐ ┌─────────────┐
│ Repo     │ │ Audit   │ │ RAG Query   │
│Connector │ │ Engine  │ │ & Analysis  │
│          │ │         │ │             │
│ GitHub/  │ │ Bandit  │ │ Vertex AI   │
│ GitLab   │ │ Radon   │ │ RAG Corpus  │
│ API      │ │         │ │ + Gemini    │
└──────────┘ └─────────┘ └─────────────┘
```

### Command Flow Examples

**Command 1: bootstrap <repo> <period>**
```
User → Agent: "Bootstrap myorg/myrepo, tags, 6 months"
Agent → RepoConnector: List tags since 6 months ago
RepoConnector → Agent: [52 tags]
Agent → AuditEngine: Audit each tag
AuditEngine → RAG: Store 52 audit reports
Agent → User: "✓ Complete. 52 audits stored. Ready for queries."
```

**Command 2: sync <repo>**
```
User → Agent: "Sync myorg/myrepo"
Agent → RAG: Get last audited SHA
RAG → Agent: "abc123 (Nov 18)"
Agent → RepoConnector: List commits since abc123
RepoConnector → Agent: [3 new commits]
Agent → AuditEngine: Audit 3 commits
AuditEngine → RAG: Store 3 new audits
Agent → User: "✓ 3 new commits. Quality: 7.2→6.8 (-5.5%)"
```

**Command 3: query <question>**
```
User → Agent: "Show security trends for myorg/myrepo"
Agent → RAG: Query audits for myorg/myrepo, focus=security
RAG → Agent: [Retrieved 52 audits]
Agent → TrendAnalyzer (Gemini): Analyze security over time
TrendAnalyzer → Agent: [Insights: SQL injection recurring...]
Agent → User: [Natural language response with trends]
```

---

## 💡 Value Proposition

### For Engineering Leads

**Problem:**
- Teams make tradeoffs on quality under pressure
- Tech debt accumulates invisibly
- No objective measure of quality trends
- Hard to justify "quality sprint" to management

**Solution:**
Independent AI auditor that:
- **Never forgets** - full history in RAG
- **Never compromises** - strict standards always
- **Shows trends** - "Quality down 15% last month"
- **Identifies patterns** - "Same security issue in 5 commits"
- **Provides evidence** - data-driven quality discussions

### Example Queries

- "How has our code quality changed since Q3?"
- "What security issues keep appearing?"
- "Which areas of the codebase have highest complexity?"
- "Are we improving or degrading over time?"
- "What should we focus on in the next sprint?"

---

## 📋 Course Concepts Coverage (6 concepts)

### Required Minimum: 3 | Our Implementation: 6

1. ✅ **Multi-Agent System**
   - Audit Orchestrator
   - Security/Complexity Analyzers
   - Query Agent
   - Trend Analyzer Agent

2. ✅ **Custom Tools**
   - GitHub API (branch monitoring)
   - Bandit (security scanner)
   - Radon (complexity analyzer)
   - Git operations

3. ✅ **Memory System (RAG)**
   - **Core differentiator**: Vertex AI RAG
   - Store complete audit history
   - Natural language queries
   - Context retrieval for trend analysis

4. ✅ **Observability**
   - Audit logging
   - Query tracing
   - Performance monitoring

5. ✅ **Evaluation**
   - LLM-as-judge for audit quality
   - Metrics: precision, recall of issues found
   - Query response accuracy

6. ✅ **Production Deployment**
   - Vertex AI Agent Engine
   - GitHub webhook integration
   - (+5 bonus points)

**Bonus:**
- Effective Use of Gemini (+5 pts) - RAG queries, trend analysis
- Agent Deployment (+5 pts) - production ready
- Video (+10 pts) - demo workflow

---

## 🛠️ Technical Implementation

### Agent 1: Audit Orchestrator
- **Trigger:** GitHub webhook (push to main/release)
- **Action:** Clone repo, run full security & complexity audit
- **Output:** Structured audit report (JSON)
- **Storage:** Send to RAG storage agent

### Agent 2: RAG Storage Agent
- **Input:** Audit report JSON
- **Action:** Convert to document, store in Vertex AI RAG Corpus
- **Metadata:** timestamp, repo, SHA, branch
- **Index:** Enable natural language queries

### Agent 3: Query Agent
- **Input:** Natural language question from user
- **Action:** Query RAG for relevant audits
- **Output:** Retrieved audit data
- **Tools:** Vertex AI RAG search

### Agent 4: Trend Analyzer Agent
- **Input:** Multiple audit reports from RAG
- **Action:** Calculate metrics trends, identify patterns
- **Output:** Insights and recommendations
- **LLM:** Gemini for synthesis

### Agent 5: Report Generator
- **Input:** Analysis from Trend Analyzer
- **Action:** Format into human-readable report
- **Output:** Natural language summary with actionable items

---

## 💡 Historical Backfill: Cold Start Solution

### The Problem
Installing Quality Guardian on a mature repository means:
- No historical data initially
- Can't answer "how did we get here?" questions
- Need weeks/months before trends appear
- Less compelling demo for competition

### The Solution: Backfill Orchestrator

**Smart scanning of historical commits with sampling strategies:**

#### Strategy 1: Tagged Releases (Recommended)
```bash
./scripts/backfill_audits.py --mode tags --since "6 months ago"
```
- Scans only version tags (v1.0.0, v2.0.0, etc.)
- **Pros:** Meaningful snapshots, low cost
- **Cons:** Uneven time spacing
- **Best for:** Well-tagged repos with semantic versioning

#### Strategy 2: Time-Based Sampling
```bash
./scripts/backfill_audits.py --mode weekly --since "1 year ago"
```
- Takes one commit per week/month
- **Pros:** Even time distribution, predictable cost
- **Cons:** May miss important releases
- **Best for:** Active repos with frequent commits

#### Strategy 3: Full History (Expensive)
```bash
./scripts/backfill_audits.py --mode full --since "3 months ago"
```
- Scans every single commit
- **Pros:** Complete data
- **Cons:** High cost, long runtime
- **Best for:** Small timeframes or critical audits

### Implementation Details

**Progress Tracking:**
- Resume capability if interrupted
- Checkpoint after each audit
- Progress bar with ETA

**Rate Limiting:**
- Respect GitHub API limits
- Configurable delay between audits
- Parallel execution for speed

**Cost Estimation:**
```python
# Before starting, show user:
"Found 52 commits to audit (tags mode, 6 months)"
"Estimated cost: $2.50 (Vertex AI + GitHub API)"
"Estimated time: 15 minutes"
"Proceed? [y/N]"
```

---

## 🔄 What We Reuse from Capstone v1

### Directly Reusable (80% of code)

✅ **Security Scanner** (`src/tools/security_scanner.py`) - works as-is  
✅ **Complexity Analyzer** (`src/tools/complexity_analyzer.py`) - works as-is  
✅ **Memory Bank** (`src/memory/review_memory.py`) - adapt for RAG storage  
✅ **Analyzer Agent** (`src/agents/analyzer.py`) - runs full repo audit  
✅ **Orchestrator** (`src/agents/orchestrator.py`) - coordinates audit flow  
✅ **Models** (`src/models.py`) - extend for audit reports  
✅ **Tests** (24 unit tests) - all still valid

### What We Port from Capstone v2

✅ **GitHub API Client** (`capstone2/src/gh_integration/client.py`) - adapt for cloning + listing commits  
✅ **Test Fixtures** (`capstone2/tests/fixtures/test_repo_manager.py`) - test repo management  

❌ **Webhook Handler** - NOT NEEDED (conversational model instead)

### What We Build New

🆕 **Main Conversational Agent** - parses commands, coordinates sub-agents  
🆕 **Repository Connector** - abstracts GitHub/GitLab/Bitbucket APIs  
🆕 **Command Parser** - understands bootstrap/sync/query intents  
🆕 **RAG Storage Manager** - stores/retrieves audits in Vertex AI  
🆕 **Trend Analyzer** - calculates quality trends with Gemini  
🆕 **Response Generator** - formats natural language answers

---

## ⏳ Implementation Timeline (10 days)

### Day 1 (Nov 21): Architecture & Design ✅
- [x] New concept definition (Quality Guardian)
- [x] Architecture design (conversational agent)
- [x] Memory Bank implementation (ADK InMemorySessionService)

### Day 2 (Nov 21): Foundation Components ✅
- [x] Audit models (CommitAudit, FileAudit) with Pydantic
- [x] AuditEngine (bandit + radon integration)
- [x] Bootstrap Handler (sampling strategies)
- [x] 170 unit tests passing

### Day 3 (Nov 21): Backend Integration ✅
- [x] GitHubConnector (GitHub API integration)
- [x] Import fixes across codebase
- [x] Backend integration demo (verified working)
- [x] 188 tests total (170 unit + 18 integration)
- [x] Documentation cleanup (archive old docs)
- [x] Diagrams updated to Quality Guardian architecture

### Days 4-5 (Nov 22-23): Orchestration Layer 🚧
- [ ] QualityGuardianAgent with ADK Agent
- [ ] Command Parser (bootstrap/sync/query with Gemini)
- [ ] RAG Corpus integration (Vertex AI)
- [ ] Store audits in persistent storage
- [ ] Demo: Full bootstrap workflow

### Days 6-7 (Nov 24-25): Query System
- Create Vertex AI RAG Corpus
- Implement RAG Storage Agent
- Store audit reports as documents
- Test retrieval queries

### Days 6-7 (Nov 26-27): Query System
- Implement Query Agent
- Implement Trend Analyzer Agent
- Build Report Generator
- End-to-end query flow

### Day 8 (Nov 28): Testing & Evaluation
- Integration tests for full workflow
- LLM-as-judge evaluation framework
- Bug fixes and refinement

### Day 9 (Nov 29): Deployment
- Deploy conversational agent to Vertex AI Agent Engine
- Create CLI client for interacting with deployed agent
- Production testing on real public repos (e.g., facebook/react)

### Day 10 (Nov 30): Documentation & Video
- Update README with new concept
- Architecture diagrams
- Record 3-min demo video
- Submit before Dec 1 deadline

---

## ✅ Success Criteria

### Technical (50 pts)
- [x] Multi-agent orchestration (5 agents)
- [x] Custom tools (GitHub, Bandit, Radon)
- [x] RAG memory system (Vertex AI)
- [x] Observability (logging, tracing)
- [x] Evaluation (LLM-as-judge)
- [x] Production deployment

### Documentation (20 pts)
- [ ] Clear problem statement
- [ ] Architecture overview
- [ ] Setup instructions
- [ ] PlantUML diagrams

### Pitch (30 pts)
- [ ] Compelling value prop for engineering leads
- [ ] Clear differentiation from Copilot
- [ ] Measurable business impact
- [ ] Innovative use of RAG for quality tracking

### Bonus (20 pts)
- [ ] Gemini integration (+5)
- [ ] Agent Engine deployment (+5)
- [ ] YouTube video (+10)

**Target: 100 points**

---

## 🎯 Winning Differentiation

### vs GitHub Copilot Code Review
- **Different audience:** Leads vs developers
- **Different timing:** Post-merge vs pre-merge
- **Different goal:** Quality trends vs PR approval

### vs Traditional Code Quality Tools
- **AI-native:** Natural language queries, not dashboards
- **Historical intelligence:** RAG-powered trend analysis
- **Management-focused:** Insights for sprint planning
- **Cold start solution:** Backfill historical data instantly

### vs Other Capstone Projects
- **Innovative RAG use:** Not just memory, but queryable history
- **Real business value:** Helps leads make data-driven decisions
- **Production-ready:** Fully deployable system
- **Instant value:** Works on mature repos from day 1 (backfill feature)

---

**Status:** Architecture complete, starting implementation  
**Confidence:** HIGH - unique concept, reuses 80% of code, clear value prop
