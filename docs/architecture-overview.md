# Architecture Overview

## System Philosophy: Intelligent Reviewer, Not Simple Linter

Our AI Code Review Orchestration System emulates **human reviewer behavior** by analyzing the complete merged state of the repository, not just isolated diff chunks.

### Key Architectural Principles

**1. Merged State Analysis**
- System applies PR to temporary repository copy
- All agents analyze the **result of the merge**, not just the diff
- Ensures comprehensive understanding of final code state

**2. Holistic Context**
- Dependency graph analysis across entire codebase
- Integration point validation (callers of modified functions)
- Backward compatibility checks

**3. Multi-Agent Coordination**
- Each agent specializes in one aspect of review
- Shared context through Memory Bank
- Orchestrator synthesizes findings into coherent review

---

## System Components

### 1. Repository Merger (Pre-processing)
- Clones base repository to temporary location
- Applies PR patch using `git apply` or equivalent
- Provides merged state path to analysis agents
- Cleanup after review completion

### 2. Multi-Agent Architecture

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
