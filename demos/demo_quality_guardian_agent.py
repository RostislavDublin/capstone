#!/usr/bin/env python3
"""Demo: Quality Guardian Agent - ADK Implementation.

This demo shows the proper ADK Agent pattern:
- Natural language commands → ADK Agent → Tool execution
- RAG Corpus integration (persistent audit storage)
- Bootstrap → Sync → Query workflow
- Proper ADK deployment-ready architecture

Using Google ADK patterns from reference materials.
"""

import asyncio
import logging
import os
import subprocess
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Suppress aiohttp unclosed session warnings from ADK internals
warnings.filterwarnings("ignore", message=".*Unclosed.*", category=ResourceWarning)

# Load environment variables
env_file = Path(__file__).parent.parent / ".env.dev"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded environment from {env_file}")
else:
    print(f"⚠️  No .env.dev found at {env_file}")

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from agent import root_agent

# Import ADK runner (proper pattern from reference notebooks)
from google.adk.runners import InMemoryRunner

# Import test repo fixture
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
from fixtures.test_repo_fixture import ensure_test_repo, get_test_repo_name

# Setup logging (minimal verbosity for clean demo output)
logging.basicConfig(
    level=logging.WARNING,  # Only warnings and errors
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Suppress verbose logs from ADK internals
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("google_adk").setLevel(logging.CRITICAL)
logging.getLogger("google.adk").setLevel(logging.CRITICAL)
logging.getLogger("google_genai").setLevel(logging.CRITICAL)
logging.getLogger("stevedore").setLevel(logging.CRITICAL)
logging.getLogger("agent").setLevel(logging.WARNING)
logging.getLogger("storage.rag_corpus").setLevel(logging.WARNING)
logging.getLogger("fixtures.test_repo_fixture").setLevel(logging.WARNING)


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def setup_test_environment():
    """Setup test repository and clean corpus."""
    print_section("🛠️  SETUP - Test Environment")
    
    print("Step 1: Ensuring test repository exists and is valid...")
    try:
        test_repo = ensure_test_repo()
        print(f"✅ Test repository ready: {test_repo}")
    except Exception as e:
        print(f"❌ Failed to setup test repo: {e}")
        logger.error("Test repo setup failed", exc_info=True)
        sys.exit(1)
    
    print("\nStep 2: Cleaning old RAG corpus for clean demo...")
    try:
        import vertexai
        from storage.rag_corpus import RAGCorpusManager
        
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("VERTEX_LOCATION", "us-west1")
        vertexai.init(project=project, location=location)
        
        # Clear files from existing corpus (faster than delete + recreate)
        try:
            rag_manager = RAGCorpusManager(corpus_name="quality-guardian-audits")
            rag_manager.initialize_corpus()
            
            files_deleted = rag_manager.clear_all_files()
            if files_deleted > 0:
                print(f"✅ Cleared {files_deleted} file(s) from corpus")
            else:
                print("ℹ️  Corpus is empty (clean slate)")
        except Exception as e:
            print(f"⚠️  Could not clear corpus: {e}")
            logger.warning(f"Corpus cleanup failed: {e}")
    except Exception as e:
        print(f"⚠️  Could not initialize Vertex AI: {e}")
    
    print("\n✅ Test environment ready!\n")


async def demo_natural_language_commands():
    """Demo: ADK Agent with natural language."""
    print_section("🤖 QUALITY GUARDIAN AGENT - ADK Implementation")
    
    print("This demo shows proper ADK Agent pattern:")
    print("  ✓ Natural language → ADK Agent → Tool execution")
    print("  ✓ RAG Corpus integration (persistent storage)")
    print("  ✓ Bootstrap → Sync → Query workflow")
    print("  ✓ Deployment-ready architecture\n")
    
    # Get test repo name
    test_repo = get_test_repo_name()
    
    # Create runner (proper ADK pattern from reference notebooks)
    runner = InMemoryRunner(agent=root_agent)
    print("✅ Agent runner ready (ADK)\n")
    
    # Test 1: Bootstrap with natural language
    print_section("TEST 1: Bootstrap Command (Natural Language)")
    
    command1 = f"Bootstrap {test_repo} with 5 commits"
    print(f"🗣️  User: '{command1}'\n")
    
    response1 = await runner.run_debug(command1)
    
    # Extract clean text response
    if isinstance(response1, list) and response1:
        last_event = response1[-1]
        if hasattr(last_event, 'content') and last_event.content.parts:
            text = last_event.content.parts[0].text if hasattr(last_event.content.parts[0], 'text') else str(response1)
            print(f"🤖 Agent: {text}\n")
    
    # Intermediate step: Add new commits to repository for sync demo
    print_section("📝 SETUP - Adding New Commits")
    print("Creating 2 new commits in test repository...")
    print("(This simulates real-world scenario where new code is pushed)\n")
    
    try:
        from fixtures.test_repo_fixture import add_test_commits
        added = add_test_commits(count=2)
        print(f"✅ Added {added} new commit(s) to {test_repo}\n")
    except Exception as e:
        print(f"⚠️  Could not add commits (repository may be read-only): {e}\n")
        print("Continuing with sync test anyway...\n")
    
    # Test 2: Sync command
    print_section("TEST 2: Sync Command (Check for New Commits)")
    
    command2 = f"Sync {test_repo}"
    print(f"🗣️  User: '{command2}'\n")
    
    response2 = await runner.run_debug(command2)
    
    # Extract clean text response
    if isinstance(response2, list) and response2:
        last_event = response2[-1]
        if hasattr(last_event, 'content') and last_event.content.parts:
            text = last_event.content.parts[0].text if hasattr(last_event.content.parts[0], 'text') else str(response2)
            print(f"🤖 Agent: {text}\n")
    
    # Test 3: Query trends
    print_section("TEST 3: Query Command (Quality Trends)")
    
    command3 = f"Show quality trends for {test_repo}"
    print(f"🗣️  User: '{command3}'\n")
    
    response3 = await runner.run_debug(command3)
    
    # Extract clean text response
    if isinstance(response3, list) and response3:
        last_event = response3[-1]
        if hasattr(last_event, 'content') and last_event.content.parts:
            text = last_event.content.parts[0].text if hasattr(last_event.content.parts[0], 'text') else str(response3)
            print(f"🤖 Agent: {text}\n")
    
    # Test 4: Natural Question
    print_section("TEST 4: Natural Question (Agent's Capabilities)")
    
    command4 = "What can you do?"
    print(f"🗣️  User: '{command4}'\n")
    
    response4 = await runner.run_debug(command4)
    
    # Extract clean text response
    if isinstance(response4, list) and response4:
        last_event = response4[-1]
        if hasattr(last_event, 'content') and last_event.content.parts:
            text = last_event.content.parts[0].text if hasattr(last_event.content.parts[0], 'text') else str(response4)
            print(f"🤖 Agent: {text}\n")


def demo_agent_composition():
    """Demo: Multi-agent composition with natural language."""
    print_section("🤖 ADK MULTI-AGENT COMPOSITION")
    
    print("This demo shows proper ADK architecture:")
    print("  ✓ Root agent → orchestrates 3 sub-agents")
    print("  ✓ Sub-agents: bootstrap_agent, sync_agent, query_agent")
    print("  ✓ Composition via AgentTool (from reference notebooks)")
    print("  ✓ Tool functions with backend logic inside (not module-level)")
    print()
    
    print("Agent architecture:")
    print(f"  Root: {root_agent.name}")
    print(f"  Tools: {len(root_agent.tools)} sub-agents")
    print()
    print("Demo complete! Agent ready for deployment.")
    print()


def interactive_mode():
    """Interactive mode: chat with the ADK agent."""
    print_section("💬 INTERACTIVE MODE - Chat with Quality Guardian")
    
    print("Type commands in natural language. Examples:")
    print("  - Bootstrap facebook/react with 10 commits")
    print("  - Sync myorg/myrepo")
    print("  - Show quality trends for myrepo")
    print("  - Type 'quit' to exit\n")
    
    # ADK agent already initialized at module level
    
    while True:
        try:
            user_input = input("🗣️  You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break
            
            print()
            response = root_agent.run(user_input)
            print(f"🤖 Agent: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            logger.error(f"Interactive mode error: {e}", exc_info=True)


def main():
    """Run demo."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  QUALITY GUARDIAN AGENT - ADK Implementation".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Proper ADK pattern with deployment-ready architecture".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("▕" + "=" * 78 + "▗")
    
    # Setup test environment first
    setup_test_environment()
    
    # Check for command line argument
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        print(f"\nRunning mode: {choice}\n")
    else:
        print("\nChoose demo mode:")
        print("  1. Natural Language Commands (automated demo)")
        print("  2. Agent Composition (show multi-agent architecture)")
        print("  3. Interactive Mode (chat with agent)")
        print("  4. Run All\n")
        choice = input("Enter choice (1-4): ").strip()
    
    try:
        
        if choice == "1":
            asyncio.run(demo_natural_language_commands())
        elif choice == "2":
            demo_agent_composition()
        elif choice == "3":
            interactive_mode()
        elif choice == "4":
            asyncio.run(demo_natural_language_commands())
            demo_agent_composition()
            print("\nWant to try interactive mode? (y/n): ", end="")
            if input().strip().lower() == "y":
                interactive_mode()
        else:
            print("Invalid choice. Running natural language demo...\n")
            asyncio.run(demo_natural_language_commands())
        
        print("\n" + "=" * 80)
        print("  ✅ Demo Complete!")
        print("=" * 80)
        print("\nWhat we demonstrated:")
        print("  ✓ Proper ADK Agent pattern (not class-based)")
        print("  ✓ Standalone tool functions with docstrings")
        print("  ✓ RAG grounding with Tool.from_retrieval()")
        print("  ✓ Deployment-ready architecture")
        print("\nNext steps:")
        print("  - Add .agent_engine_config.json for deployment")
        print("  - Deploy to Cloud Run via Agent Engine")
        print("  - Add observability and evaluation\n")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
