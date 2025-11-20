# Code Review Assistant - Final Project Plan

**Project Name:** AI Code Review Orchestration System  
**Tagline:** "Closing the AI Feedback Loop in Modern Development Workflows"  
**Track:** Enterprise Agents  
**Target Score:** 95-100 points  
**Timeline:** Nov 18 → Dec 1, 2025 (13 days)

---

## 🎯 Strategic Positioning (Trend-Aligned)

### Market Context (Nov 2025):
- **GitHub Agent HQ** (Oct 28): Platform for agent orchestration in dev workflows
- **Octoverse 2025** (Nov 7): 986M code pushes, AI-generated code volume exploding
- **Google Memory for Code Reviews**: Gemini Code Assist getting memory capabilities
- **Agent Sandbox on GKE**: Production deployment focus for enterprise agents

### Our Position:
"Multi-agent orchestration system that closes the AI feedback loop: while GitHub Copilot generates code at AI speed, our agents review it at the same pace - using Google's latest Gemini memory capabilities."

### Key Messaging:
1. **Complements GitHub Copilot** (not competes) - Copilot writes → We review
2. **Agent Orchestration** - Multiple specialized agents working together (like Agent HQ)
3. **Memory-Enhanced** - Context retention using Google's latest capabilities
4. **Enterprise Production-Ready** - Deployed on Agent Engine with security

---

## 🏗️ Technical Architecture

### Multi-Agent System (3 Agents):

**1. Analyzer Agent**
- **Role:** Primary code analysis and issue detection
- **Tools:** 
  - Git diff parser
  - Static analysis (AST parsing)
  - Code quality metrics
- **Output:** List of issues, suggestions, severity levels

**2. Context Agent**
- **Role:** Gather historical context and institutional knowledge
- **Tools:**
  - GitHub API (previous PR comments, review patterns)
  - Memory Bank (ADK) - retained learnings
  - Code standards retrieval
- **Output:** Relevant context for current review

**3. Reporter Agent**
- **Role:** Generate human-readable review summaries
- **Tools:**
  - GitHub API (post comments)
  - Ticket creation (optional: Jira/GitHub Issues)
  - Markdown formatting
- **Output:** Formatted review comments, action items

### Agent Orchestration:
```
PR Event (webhook)
    ↓
Analyzer Agent (parallel with Context Agent)
    ↓                    ↓
  Issues           Context/History
    ↓                    ↓
    └──> Reporter Agent ───> GitHub Comment + Summary
```

---

## 📋 Course Concepts Coverage (6 concepts)

### Required Minimum: 3 | Our Implementation: 6

1. ✅ **Multi-Agent System** (parallel agents with orchestration)
2. ✅ **Custom Tools** (GitHub API, git parser, static analysis)
3. ✅ **Memory System** (Memory Bank for review patterns, ADK InMemorySessionService)
4. ✅ **Observability** (Logging for each agent, tracing review flow)
5. ✅ **Evaluation** (LLM-as-judge for review quality, automated metrics)
6. ✅ **Agent Deployment** (Vertex AI Agent Engine, production-ready)

**Bonus:**
- A2A Protocol (optional: if agents communicate via protocol)
- Sessions & State Management (InMemorySessionService)

---

## 🛠️ Technical Implementation Details

### Stack:
- **Framework:** Google ADK (Python)
- **LLM:** Gemini 2.5 Flash (fast) + Gemini 2.5 Pro (complex analysis)
- **Memory:** ADK Memory Bank + InMemorySessionService
- **Tools:** GitHub API, PyGithub, GitPython, AST parser
- **Deployment:** Vertex AI Agent Engine
- **Observability:** ADK logging + Cloud Logging

### Key Features:

**1. Memory System (Google's latest focus):**
- Store accepted/rejected review suggestions
- Learn team's coding standards
- Remember common issue patterns
- Context retention across PRs

**2. GitHub Integration (Copilot complement):**
- Webhook for PR events
- Comment on PRs with findings
- Link to relevant documentation
- Track review acceptance rate

**3. Quality Analysis:**
- Code complexity metrics
- Security vulnerability scanning (basic)
- Style consistency checks
- Test coverage analysis

**4. Smart Reporting:**
- Severity-based prioritization
- Actionable suggestions with code examples
- Link to previous similar issues
- Estimated fix time

---

## 📊 Evaluation & Testing

### Evaluation Framework:

**1. LLM-as-Judge:**
- Review quality scoring
- Suggestion relevance
- False positive rate
- Tone appropriateness

**2. Automated Metrics:**
- Review completion time
- Issue detection accuracy (vs manual review)
- Memory recall accuracy
- Agent orchestration latency

**3. Test Cases:**
- Real PRs from open-source projects
- Synthetic PRs with known issues
- Edge cases (empty diffs, huge PRs)
- Memory persistence tests

### Evalset Structure:
```json
{
  "queries": [
    {
      "pr_url": "...",
      "expected_issues": ["security", "complexity"],
      "expected_suggestions": 3
    }
  ]
}
```

---

## 📝 Documentation Plan

### README.md Structure:

1. **Introduction**
   - Market context (GitHub Agent HQ, Octoverse data)
   - Problem statement (AI code volume → review bottleneck)
   - Solution overview

2. **Architecture**
   - Multi-agent system diagram
   - Agent responsibilities
   - Orchestration flow
   - Memory system design

3. **Technical Implementation**
   - Course concepts demonstrated
   - Technology choices (ADK, Gemini, Memory Bank)
   - GitHub integration details

4. **Setup & Deployment**
   - Prerequisites
   - Configuration (GitHub token, GCP project)
   - Local testing
   - Production deployment to Agent Engine

5. **Usage & Demo**
   - Example PR review
   - Screenshots of agent in action
   - Before/after comparison

6. **Evaluation & Results**
   - Test methodology
   - Quality metrics
   - Performance benchmarks

7. **Future Enhancements**
   - Additional language support
   - IDE integration
   - Team analytics dashboard

### Diagrams Needed:
- [ ] Architecture diagram (3 agents + orchestration)
- [ ] Sequence diagram (PR → Review flow)
- [ ] Memory system design
- [ ] GitHub integration workflow

---

## 🎬 Video Script (3 minutes)

### Structure:

**0:00-0:30 - Hook & Context (30 sec)**
```
"In October 2025, GitHub launched Agent HQ - the future of AI agent 
orchestration in development. But there's a critical gap: while Copilot 
generates code at AI speed, human review is now the bottleneck. 
According to GitHub's 2025 Octoverse, we're seeing 986 million code 
pushes - and AI-generated code is exploding. We need to close this loop."
```

**0:30-1:00 - Problem Deep Dive (30 sec)**
```
"The problem is clear: AI writes code faster than humans can review it. 
Teams are stuck with a choice - slow down AI generation, or compromise 
on review quality. Neither is acceptable for production systems. 
This is where agent orchestration comes in."
```

**1:00-1:45 - Solution & Architecture (45 sec)**
```
"Meet our AI Code Review Orchestration System - three specialized agents 
working together using Google's ADK and latest Gemini memory capabilities.

[Show diagram]
- Analyzer Agent examines code for issues
- Context Agent retrieves historical patterns using Memory Bank
- Reporter Agent generates actionable reviews

Built on Vertex AI Agent Engine, this isn't a demo - it's production-ready."
```

**1:45-2:30 - Demo (45 sec)**
```
[Screen recording]
"Watch as a PR triggers the workflow: 
- Real-time code analysis detecting complexity and security issues
- Memory system recalling team coding standards
- Formatted review posted directly to GitHub
All in under 10 seconds."
```

**2:30-3:00 - Value & Technical Depth (30 sec)**
```
"This demonstrates 6 key concepts from the course: multi-agent systems, 
custom tools, memory, observability, evaluation, and production deployment.

The result? Teams review code 70% faster with consistent quality. 
We're not replacing human judgment - we're augmenting it at AI speed.

Closing the AI feedback loop. Built with ADK. Production-ready today."
```

---

## 📅 Implementation Timeline (13 days)

### Phase 1: Design & Setup (Nov 18-19)

**Day 1 - TODAY (Nov 18):**
- [x] Market research & trend analysis
- [x] Final project plan
- [ ] Architecture diagram design
- [ ] Agent interaction design
- [ ] Tool interface specifications
- [ ] Create project structure

**Day 2 (Nov 19):** ✅ **COMPLETED**
- [x] GitHub API research & auth setup
- [x] Memory Bank schema design
- [x] Evalset design (test cases with changeset references)
- [x] **Testing infrastructure redesign** (unified changeset approach)
- [x] **Created changesets.py** (single source of truth for all tests)
- [x] **Created diff_generator.py** (synthetic diffs for local testing)
- [x] **Created mock_pr_context.py** (PullRequest objects for testing)
- [x] **Updated create_test_prs.py** (applies changesets to GitHub)
- [x] **Updated evalset** (references changesets via changeset_id)
- [x] **Created comprehensive unit tests** (test_changesets.py)
- [x] **Complete testing documentation** (testing-strategy.md, unified-testing-architecture.md)
- [x] Set up development environment

### Phase 2: Core Implementation (Nov 20-25)

**Day 3 (Nov 20) - Analyzer Agent:**
- [ ] Git diff parsing
- [ ] Basic code analysis (complexity, style)
- [ ] Issue detection logic
- [ ] Gemini integration for semantic analysis

**Day 4 (Nov 21) - Analyzer Agent cont.:**
- [ ] AST parsing for deeper analysis
- [ ] Security pattern detection
- [ ] Output formatting
- [ ] Unit tests

**Day 5 (Nov 22) - Context Agent:**
- [ ] GitHub API integration
- [ ] Fetch previous PR reviews
- [ ] Memory Bank setup
- [ ] Context retrieval logic

**Day 6 (Nov 23) - Context Agent cont.:**
- [ ] Memory persistence
- [ ] Learning from feedback
- [ ] Context relevance scoring
- [ ] Integration tests

**Day 7 (Nov 24) - Reporter Agent:**
- [ ] Review summary generation
- [ ] GitHub comment formatting
- [ ] Severity prioritization
- [ ] Markdown output

**Day 8 (Nov 25) - Orchestration:**
- [ ] Agent coordination logic
- [ ] Sequential workflow
- [ ] Error handling
- [ ] Retry mechanisms

### Phase 3: Quality & Evaluation (Nov 26-27)

**Day 9 (Nov 26) - Testing:**
- [ ] Evaluation framework setup
- [ ] LLM-as-judge implementation
- [ ] Run evalsets on test PRs
- [ ] Bug fixes based on results

**Day 10 (Nov 27) - Observability:**
- [ ] Logging for each agent
- [ ] Tracing setup
- [ ] Performance metrics
- [ ] Test on real repos

### Phase 4: Deployment & Docs (Nov 28-29)

**Day 11 (Nov 28) - Deployment:**
- [ ] Deploy to Agent Engine
- [ ] Webhook setup for GitHub
- [ ] Test deployed agent
- [ ] Performance tuning

**Day 12 (Nov 29) - Documentation:**
- [ ] Complete README.md
- [ ] Architecture diagrams (finalize)
- [ ] Setup instructions
- [ ] Usage examples with screenshots
- [ ] Evaluation results write-up

### Phase 5: Video & Submission (Nov 30-Dec 1)

**Day 13 (Nov 30) - Video:**
- [ ] Record demo (screen + voiceover)
- [ ] Edit video (keep under 3 min)
- [ ] Upload to YouTube
- [ ] Create thumbnail

**Day 14 (Dec 1) - SUBMIT:**
- [ ] Final README review
- [ ] Writeup draft (<1500 words)
- [ ] Title + subtitle creation
- [ ] Card/thumbnail image
- [ ] Submit to Kaggle (morning, buffer time)

---

## ✅ Success Criteria Checklist

### Technical Implementation (50 pts target):
- [ ] Multi-agent system with 3 agents
- [ ] Analyzer Agent (git diff, static analysis, Gemini)
- [ ] Context Agent (GitHub API, Memory Bank)
- [ ] Reporter Agent (summary generation, comments)
- [ ] Sequential orchestration with error handling
- [ ] Custom tools (GitHub API, git parser)
- [ ] Memory Bank for pattern retention
- [ ] InMemorySessionService for state
- [ ] Logging and tracing throughout
- [ ] LLM-as-judge evaluation
- [ ] Automated metrics (speed, accuracy)
- [ ] Clean code with comprehensive comments
- [ ] Agents are central to solution (not bolt-on)

### Documentation (20 pts target):
- [ ] Professional README.md
- [ ] Architecture diagram (3 agents + flow)
- [ ] Sequence diagram (PR review process)
- [ ] Memory system design diagram
- [ ] Problem statement (with market context)
- [ ] Solution description (agent orchestration)
- [ ] Setup instructions (step-by-step)
- [ ] Usage examples (real PR demos)
- [ ] Evaluation results (metrics, charts)
- [ ] Screenshots of agent in action

### Pitch/Writeup (25+ pts target):
- [ ] Clear problem articulation (AI bottleneck)
- [ ] Market validation (GitHub Agent HQ, Octoverse)
- [ ] Innovative solution (agent orchestration)
- [ ] Enterprise track alignment
- [ ] Quantifiable value ("70% faster reviews")
- [ ] Compelling narrative (closing AI feedback loop)
- [ ] Technical depth appropriate
- [ ] Well-written (<1500 words)

### Bonus (20 pts target):
- [ ] Uses Gemini 2.5 (5 pts) - already using
- [ ] Deployed to Agent Engine (5 pts) - will deploy
- [ ] YouTube video <3min (10 pts) - will create
  - [ ] Problem statement
  - [ ] Why agents?
  - [ ] Architecture diagram
  - [ ] Live demo
  - [ ] Build process

### Submission Requirements:
- [ ] Public GitHub repo
- [ ] Catchy title
- [ ] One-line subtitle
- [ ] Card/thumbnail image
- [ ] Project description (<1500 words)
- [ ] YouTube video URL
- [ ] Submitted before Dec 1, 11:59 AM PT

---

## 🎯 Risk Mitigation

### Technical Risks:

**Risk:** GitHub API rate limits  
**Mitigation:** Cache responses, use webhooks not polling, test with small repos

**Risk:** Memory Bank complexity  
**Mitigation:** Start with InMemorySessionService, add persistence incrementally

**Risk:** Agent orchestration bugs  
**Mitigation:** Extensive logging, test each agent independently first

**Risk:** Deployment issues  
**Mitigation:** Deploy early (Day 11), leave 3 days buffer

### Timeline Risks:

**Risk:** Scope creep  
**Mitigation:** Strict feature freeze after Day 8, focus on polish

**Risk:** Video takes too long  
**Mitigation:** Record as we build, edit on Day 13 only

**Risk:** Submission issues  
**Mitigation:** Submit morning of Dec 1, not last minute

### Quality Risks:

**Risk:** Poor evaluation results  
**Mitigation:** Test continuously, iterate on quality from Day 9

**Risk:** Unclear documentation  
**Mitigation:** Write docs alongside code, get feedback early

---

## 📊 Success Metrics

### Target Outcomes:

**Technical:**
- Review generation time: <15 seconds per PR
- Issue detection accuracy: >80% vs manual review
- Memory recall accuracy: >90% for known patterns
- False positive rate: <20%

**Evaluation:**
- LLM-as-judge score: >8/10 for review quality
- All evalset test cases: PASS
- Deployed agent uptime: 99%+

**Competition:**
- Rubric score: 95-100 points
- Finish: Top-3 in Enterprise Agents track

---

## 🚀 Next Immediate Actions

### Today (Nov 18):
1. Create project structure in `/src/capstone/`
2. Design architecture diagrams (draw.io or similar)
3. Set up GitHub test repository for demos
4. Research GitHub API authentication
5. Design Memory Bank schema

### Tomorrow (Nov 19):
1. Implement basic agent scaffolding
2. GitHub API integration testing
3. Create initial evalset
4. Start README outline
5. Set up GCP project for deployment

---

## 🎉 Day 2 Achievements (Nov 19, 2025)

### Major Architectural Decision: Unified Changeset Testing

**Problem Identified:**
- Initial design had separate test definitions for local vs remote testing
- Would lead to duplication and maintenance overhead
- Violates DRY principle

**Solution Implemented:**
Created unified changeset architecture where:
- ✅ Single source of truth: `changesets.py` defines all test scenarios
- ✅ Same definitions work for local unit tests AND remote E2E tests
- ✅ Changesets contain code, expected issues, PR metadata, test criteria
- ✅ Easy to extend: add one changeset → works everywhere

### Files Created (8 files, ~1,500 lines):

1. **changesets.py** (426 lines)
   - Changeset and ExpectedIssue Pydantic models
   - 4 complete changeset definitions
   - Registry structures and helper functions
   - SOURCE OF TRUTH for all testing

2. **tools/diff_generator.py** (200+ lines)
   - Generate synthetic git diffs from changesets
   - Supports add/modify/replace operations
   - No git required for unit tests

3. **tools/mock_pr_context.py** (180+ lines)
   - Create PullRequest objects from changesets
   - Mock author, metadata, diff, files
   - Enables integration tests without GitHub API

4. **tests/test_changesets.py** (280+ lines)
   - Comprehensive unit tests for infrastructure
   - 6 test classes covering all aspects
   - Example tests for future agent development

5. **docs/testing-strategy.md** (300+ lines)
   - Complete guide to testing approach
   - Local, Remote, Sequential test modes
   - Examples and workflows

6. **docs/unified-testing-architecture.md** (240+ lines)
   - Architecture overview and rationale
   - Workflow examples
   - Adding new test cases guide

7. **scripts/create_test_prs.py** - UPDATED
   - Now uses changesets from changesets.py
   - apply_changeset() method
   - Automatic PR body generation from expected_issues

8. **evalsets/test_fixture_prs.evalset.json** - UPDATED
   - Added changeset_id field linking to changesets
   - Version bumped to 2.0.0

### Key Insights Gained:

1. **Copilot Edits UI vs Git:**
   - create_file tool writes directly to disk
   - Keep/Undo operates at VS Code workspace level
   - Independent of git workflow

2. **Test Fixture Strategy:**
   - test-fixture/ = static frozen bad code (never changes locally)
   - Changesets = definitions of modifications to apply
   - Same changesets for both local synthetic diffs and remote PR creation

3. **Testing Modes:**
   - Unit: Fast, no network, synthetic diffs
   - Integration: Mock GitHub API, full agent behavior
   - E2E: Real GitHub PRs created from changesets
   - Sequential: Memory Bank learning evaluation

4. **Benefits of Unified Approach:**
   - No duplication between test modes
   - Single update propagates everywhere
   - Consistent expected outcomes
   - Easy maintenance and extension

### What's Next (Day 3):

1. Begin Analyzer Agent implementation
2. Git diff parsing tools
3. Basic code analysis (complexity, style)
4. Security pattern detection
5. Gemini integration for semantic analysis

**Ahead of schedule:** Testing infrastructure complete allows rapid agent development.

---

**Project Lead:** Rostislav Dublin  
**Framework:** Google ADK  
**Target:** Top-3 Enterprise Agents Track  
**Status:** Ready to implement  
**Confidence:** HIGH

**Last Updated:** November 18, 2025
