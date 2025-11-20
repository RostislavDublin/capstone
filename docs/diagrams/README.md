# Architecture Diagrams

This directory contains PlantUML diagrams for the AI Code Review Orchestration System.

## Diagrams

### 1. Multi-Agent Architecture (`multi-agent-architecture.puml`)
Shows the overall system architecture with three specialized agents, tools, and external integrations.

**Key Components:**
- Review Orchestrator (event handling, coordination)
- Analyzer Agent (code analysis, issue detection)
- Context Agent (history retrieval, pattern matching)
- Reporter Agent (summary generation, comment formatting)
- Custom Tools (GitHub API, git parser, static analysis)
- Memory Bank (persistent storage)

### 2. Sequence Flow (`sequence-flow.puml`)
Illustrates the complete code review process from PR creation to review posting.

**Flow Stages:**
1. PR Creation & Webhook
2. Parallel Analysis (Analyzer + Context)
3. Results Aggregation
4. Report Generation
5. Memory Update
6. GitHub Posting
7. Learning Loop (feedback)

**Timing:** Total < 15 seconds

### 3. Memory System (`memory-system.puml`)
Details the Memory Bank architecture for context retention and learning.

**Components:**
- Pattern Storage (review patterns, acceptance rates)
- Team Knowledge (coding standards, best practices)
- Historical Data (previous reviews, changes)
- Learning Module (feedback processing, weight adjustment)

**Storage Types:**
- Session Store (in-memory, temporary)
- Persistent Store (Memory Bank, long-term)

### 4. Deployment Architecture (`deployment.puml`)
Production deployment on Google Cloud Platform.

**Infrastructure:**
- Vertex AI Agent Engine
- Cloud Run (container runtime)
- Cloud Storage (Memory Bank)
- Cloud Logging (observability)
- Gemini API (LLM backend)

## Viewing Diagrams

### Online Viewers
- [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
- [PlantText](https://www.planttext.com/)

### VS Code Extension
Install: [PlantUML Extension](https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml)

### Command Line
```bash
# Install PlantUML
brew install plantuml  # macOS
apt install plantuml   # Linux

# Generate PNG
plantuml multi-agent-architecture.puml

# Generate SVG
plantuml -tsvg multi-agent-architecture.puml
```

### Docker
```bash
docker run -v $(pwd):/data plantuml/plantuml -tpng /data/*.puml
```

## Generating Images

To generate PNG images for all diagrams:

```bash
cd docs/diagrams
plantuml *.puml
```

This will create:
- `multi-agent-architecture.png`
- `sequence-flow.png`
- `memory-system.png`
- `deployment.png`

## Embedding in Documentation

Images can be referenced in Markdown:

```markdown
![Multi-Agent Architecture](docs/diagrams/multi-agent-architecture.png)
```

Or use PlantUML URL encoding for GitHub:
```markdown
![Architecture](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/RostislavDublin/ai/main/src/capstone/docs/diagrams/multi-agent-architecture.puml)
```

## Notes

All diagrams follow the ADK course concepts:
- ✅ Multi-agent systems
- ✅ Custom tools
- ✅ Memory & sessions
- ✅ Observability
- ✅ Production deployment
