# ADK Web Agents

This directory contains ADK web-compatible agent wrappers for Quality Guardian.

## Structure

Each subdirectory represents a separate agent that can be run with `adk web`:

```
adk_agents/
├── quality_guardian/    # Main orchestrator (uses all sub-agents)
├── bootstrap/           # Initial repository analysis
├── sync/                # Check for new commits
└── query/               # Quality trends analysis
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

4. **query** - Standalone query agent
   - Answers questions about quality trends
   - Example: "Show quality trends for facebook/react"

## Implementation Details

Each agent directory follows ADK web convention:
- `__init__.py` - Package initialization
- `agent.py` - Entry point with `root_agent` variable

The actual agent logic resides in `src/agents/` directory. These wrappers simply import and expose the agents for ADK web compatibility.
