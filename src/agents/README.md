# ADK Web Agents

This directory contains ADK web-compatible agent wrappers for Quality Guardian.

## Structure

Each subdirectory represents a separate agent that can be run with `adk web`:

```
agents/
├── quality_guardian/      # Main orchestrator (uses all sub-agents)
├── bootstrap/             # Initial repository analysis
├── sync/                  # Check for new commits
├── query_orchestrator/    # Routes queries to specialized agents
├── query_trends/          # Quality trends (Firestore)
└── query_root_cause/      # Root cause analysis (RAG semantic search)
```

## Usage

### Run all agents (recommended)

```bash
cd src
adk web adk_agents
```

This will start a web interface where you can select and interact with any agent.

### Run specific agent

```bash
cd src
adk web adk_agents/quality_guardian
```

### Available Agents

1. **quality_guardian** - Full multi-agent system
   - Orchestrates bootstrap, sync, and query agents
   - Best choice for complete functionality

2. **bootstrap** - Standalone bootstrap agent
   - Analyzes repository for first time
   - Example: "Bootstrap facebook/react with 10 commits"

3. **sync** - Standalone sync agent
   - Checks for new commits
   - Example: "Sync facebook/react"

4. **query_orchestrator** - Query router (RECOMMENDED)
   - Routes to trends or root cause agents
   - Supports composite queries (trends + root cause)
   - Example: "Show trends and explain why quality dropped"

5. **query_trends** - Quality trend analysis
   - Uses Firestore for structured queries
   - Example: "Show quality trends for facebook/react"

6. **query_root_cause** - Root cause analysis (RAG)
   - Uses Vertex AI RAG semantic search
   - Example: "Why did quality drop? Find root causes"

## Implementation Details

Each agent directory follows ADK web convention:
- `__init__.py` - Package initialization
- `agent.py` - Entry point with `root_agent` variable

The actual agent logic resides in `src/agents/` directory. These wrappers simply import and expose the agents for ADK web compatibility.
