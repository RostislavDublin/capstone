# Architecture Diagrams - Quality Guardian

**Last Updated:** November 21, 2025 (Day 3)  
**Status:** ✅ All diagrams updated to Quality Guardian architecture

This directory contains PlantUML diagrams for the Repository Quality Guardian system.

## Diagrams

### 1. Multi-Agent Architecture (`multi-agent-architecture.puml.md`)

Shows the overall system architecture and component relationships.

**Key Components:**
- Engineering Lead (user)
- Quality Guardian Agent (orchestrator with Gemini 2.0 Flash)
- Backend Tools:
  - GitHub Connector (repo API + commit fetcher)
  - Audit Engine (bandit + radon + temp checkout)
  - Query Agent (RAG retrieval + Gemini 2.5 Pro)
- Vertex AI RAG Corpus (persistent audit storage)

**Use Case:** Understanding high-level architecture

---

### 2. Sequence Flow (`sequence-flow.puml.md`)

Illustrates three command workflows: bootstrap, sync, and query.

**Flow Stages:**

**Command 1: Bootstrap** (Historical Scan)
1. User requests bootstrap with time range
2. Agent fetches commit list from GitHub
3. Agent audits each commit with AuditEngine
4. Agent stores audits in RAG Corpus
5. Agent returns summary to user

**Command 2: Sync** (Incremental Update)
1. Agent queries RAG for last audited SHA
2. Agent fetches new commits from GitHub
3. Agent audits new commits
4. Agent calculates quality delta
5. Agent returns trend metrics

**Command 3: Query** (Insights)
1. User asks about quality trends
2. Query Agent retrieves relevant audits from RAG
3. Query Agent analyzes with Gemini
4. Agent returns insights + recommendations

---

### 3. Memory System (`memory-system.puml.md`)

**Note:** This diagram is from Day 1 Memory Bank implementation. The concept evolved into RAG Corpus for Quality Guardian, but the ADK InMemorySessionService pattern is still used for session state.

**Status:** Kept for reference (original implementation)

---

### 4. Deployment Architecture (`deployment.puml.md`)

Production deployment on Google Cloud Platform.

**Infrastructure:**
- Vertex AI Agent Engine (Quality Guardian + Query Agent)
- Gemini 2.0 Flash (command parsing)
- Gemini 2.5 Pro (trend analysis)
- Vertex AI RAG Corpus (audit history)
- Supporting Services (Logging, Secrets, Monitoring, IAM)
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
