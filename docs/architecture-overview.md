# Architecture Overview - Quality Guardian

## System Philosophy: Independent Quality Auditor

The **Repository Quality Guardian** is an independent AI auditor that monitors release branch commits, maintains comprehensive audit history in RAG, and provides engineering leads with data-driven quality insights.

### Key Architectural Principles

**1. Full Repository Auditing**
- Monitors commits to release branches (main/production/etc)
- Analyzes **complete repository state** after each commit
- Provides objective quality assessment regardless of team practices

**2. Historical Intelligence via RAG**
- Every audit stored in Vertex AI RAG Corpus
- Natural language queries: "How has quality changed?"
- Trend analysis across weeks/months/quarters

**3. Management-Focused Output**
- Target audience: Engineering leads, PMs, Team Leads
- Not involved in PR discussions or developer workflow
- Provides evidence for sprint planning and quality initiatives

**4. Multi-Agent Orchestration**
- **INPUT agents:** Audit on every commit (automated)
- **OUTPUT agents:** Answer quality queries (on-demand)
- **Storage layer:** RAG for persistent memory

---

## System Architecture: Conversational Agent Model

**Key Design Decision:** No webhooks. User-driven, conversational interaction.

**Why This Approach:**
- ✅ Works with any Git hosting (GitHub, GitLab, Bitbucket, Azure DevOps)
- ✅ No infrastructure setup required (webhooks, public endpoints)
- ✅ User controls when audits happen
- ✅ Simpler deployment (just agent + RAG)
- ✅ Better for demos and presentations

### Three Commands

The agent understands natural language but primarily responds to three command patterns:

---

### Command 1: `bootstrap` - Initial Historical Scan

**User Request Examples:**
- "Connect to myorg/myrepo and bootstrap the last 6 months"
- "Scan facebook/react using tagged releases from 2024"
- "Initialize audit history for microsoft/vscode, weekly snapshots, past year"

**Agent Flow:**
1. Parse repository URL (GitHub/GitLab/Bitbucket)
2. Authenticate using stored token
3. Use Git API to list commits matching criteria:
   - **Tags mode:** Only version tags (v1.0.0, v2.0.0, etc.)
   - **Time-based:** Weekly/monthly snapshots
   - **Full:** Every commit (expensive)
4. For each commit:
   - Clone repository at that SHA via API
   - Run security (Bandit) and complexity (Radon) analysis
   - Generate audit report with historical timestamp
   - Store in Vertex AI RAG Corpus
5. Report progress and summary

**Output:** 
```
✓ Bootstrapped myorg/myrepo (52 commits audited)
  - Date range: 2024-06-01 to 2024-11-21
  - Security issues found: 23 (8 critical, 15 major)
  - Avg complexity: B+ (trending down)
  - Ready for queries
```

---

### Command 2: `sync` - Incremental Update

**User Request Examples:**
- "Check myorg/myrepo for new commits"
- "Sync audit for facebook/react"
- "Update audit history - any new commits since last check?"

**Agent Flow:**
1. Query RAG for last audited commit SHA for this repo
2. Use Git API to fetch commits since that SHA
3. If new commits found:
   - Audit each new commit (same process as bootstrap)
   - Store new audits in RAG
   - Calculate delta metrics
4. If no new commits: report "up to date"

**Output:**
```
✓ Synced myorg/myrepo
  - 3 new commits since last audit (Nov 18)
  - Quality score: 7.2 → 6.8 (degraded 5.5%)
  - New issues: 2 critical security vulnerabilities
  - Recommendation: Review commits abc123, def456
```

---

### Command 3: `query` - Quality Insights

**User Request Examples:**
- "How has quality changed in myorg/myrepo over last quarter?"
- "Show me security trends for facebook/react"
- "What are the persistent issues in microsoft/vscode?"
- "Which areas need refactoring in tensorflow/tensorflow?"

**Agent Flow:**
1. **Query Understanding:** Parse question to identify:
   - Target repository
   - Time range
   - Focus area (security/complexity/trends)
2. **RAG Retrieval:** Query Vertex AI RAG for relevant audits
3. **Trend Analysis:** Use Gemini to:
   - Compare metrics across time
   - Identify patterns and anomalies
   - Spot recurring issues
4. **Report Generation:** Format insights with:
   - Trend summary
   - Specific examples
   - Actionable recommendations

**Output:**
```
Quality Trends for myorg/myrepo (Q3 2024)

📉 Overall: Quality degraded 12% (8.1 → 7.1)

🔴 Security: 
  - SQL injection pattern in 4 of 6 recent audits
  - Files: api/auth.py, api/db.py
  
📊 Complexity:
  - avg_complexity: B → C+ (trending worse)
  - Hotspot: services/payment.py (CC=42)
  
💡 Recommendations:
  1. Security audit on database layer (priority: high)
  2. Refactor payment service (split into smaller functions)
  3. Add input validation standards
```

---

## System Components

### Core Agent: Conversational Quality Guardian

**Deployed on:** Vertex AI Agent Engine  
**Interface:** Natural language (text-based)  
**Access:** Works with public repos or private repos with API token

#### Main Agent Responsibilities
1. **Command parsing:** Understand `bootstrap`, `sync`, `query` intents
2. **Repository access:** GitHub/GitLab/Bitbucket API integration
3. **Audit orchestration:** Coordinate analysis tools
4. **RAG interaction:** Store and retrieve audit history
5. **Response generation:** Natural language answers with data

---

### Sub-Agents and Tools

#### 1. Repository Connector Tool
- **Purpose:** Abstract Git hosting platform differences
- **Supports:** GitHub, GitLab, Bitbucket APIs
- **Capabilities:**
  - List commits with filtering
  - Clone repo at specific SHA
  - Fetch metadata (tags, branches, authors)
- **Authentication:** Token-based (stored securely)

#### 2. Audit Engine
- **Trigger:** bootstrap or sync command
- **Flow:**
  - Receives commit SHA from Repository Connector
  - Clones code via API
  - Runs parallel analysis:
    * Security Scanner (Bandit)
    * Complexity Analyzer (Radon)
  - Generates structured audit report
- **Output:** JSON audit document

#### 3. Security Scanner (Bandit)
- **Tool:** Bandit static analysis
- **Analysis:** Hardcoded secrets, SQL injection, unsafe deserialization
- **Output:** List of security issues with severity (CRITICAL/MAJOR/MINOR)

#### 4. Complexity Analyzer (Radon)
- **Tool:** Radon cyclomatic complexity
- **Analysis:** Function complexity, maintainability index
- **Output:** Complexity metrics per file/function

#### 5. RAG Storage Manager
- **Responsibility:** Persist audits in Vertex AI RAG Corpus
- **Operations:**
  - Store new audit documents
  - Query by repository, date range, keywords
  - Retrieve audit history for trend analysis
- **Indexing:** By timestamp, commit SHA, repository name, issue types
- **Metadata:** Enables temporal and semantic queries

#### 6. Trend Analyzer
- **Trigger:** User query command
- **Input:** Multiple audits from RAG
- **Processing:**
  - Compare metrics over time (security, complexity, quality score)
  - Identify recurring issues (same pattern in N audits)
  - Calculate trajectories (improving/degrading)
  - Spot anomalies (sudden quality drops)
- **LLM:** Gemini 2.5 Flash for pattern recognition
- **Output:** Structured insights (trends, hotspots, recommendations)

#### 7. Response Generator
- **Input:** Analysis from Trend Analyzer
- **Processing:** Format into natural language
- **Features:**
  - Executive summary
  - Data visualization (text-based charts)
  - Specific examples with file paths
  - Actionable recommendations
- **Output:** Human-readable response

### 3. Multi-Agent Architecture

Overall system architecture showing three agents and orchestration:

@import "diagrams/multi-agent-architecture.puml.md"

## Sequence Flow

PR review workflow sequence diagram:

@import "diagrams/sequence-flow.puml.md"

## Memory System

Memory Bank architecture and data flow:

@import "diagrams/memory-system.puml.md"

## Deployment

Production deployment on Vertex AI Agent Engine:

@import "diagrams/deployment.puml.md"

---

**Note:** Use Markdown Preview Enhanced (Cmd+K V or Cmd+Shift+V) to see rendered diagrams.
