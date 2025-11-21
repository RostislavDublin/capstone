#!/usr/bin/env python3
"""Demo: Quality Guardian Agent - Natural Language Interface.

This demo shows the REAL agent orchestration (not just backend tools):
- Natural language commands → Gemini parsing → Tool execution
- RAG Corpus integration (persistent audit storage)
- Bootstrap → Sync → Query workflow

Progress: ~40% (orchestration layer working!)
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

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

from agents.quality_guardian_v2 import QualityGuardianAgentV2

# Import test repo fixture
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
from fixtures.test_repo_fixture import ensure_test_repo, get_test_repo_name

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


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
        from vertexai.preview import rag
        
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("VERTEX_LOCATION", "us-west1")
        vertexai.init(project=project, location=location)
        
        # Delete ALL corpuses with "quality-guardian" in name
        try:
            corpuses = list(rag.list_corpora())
            deleted_count = 0
            for corpus in corpuses:
                if "quality-guardian" in corpus.display_name.lower():
                    print(f"   Deleting corpus: {corpus.display_name}")
                    files = list(rag.list_files(corpus_name=corpus.name))
                    print(f"     (removing {len(files)} files)")
                    rag.delete_corpus(name=corpus.name)
                    deleted_count += 1
            
            if deleted_count > 0:
                print(f"✅ Deleted {deleted_count} old corpus(es)")
                # Wait for Vertex AI to propagate deletion (backend cache invalidation)
                import time
                print("   Waiting for deletion to propagate (10 seconds)...")
                time.sleep(10)
            else:
                print("ℹ️  No old corpus found (clean slate)")
        except Exception as e:
            print(f"⚠️  Could not delete corpus: {e}")
            logger.warning(f"Corpus cleanup failed: {e}")
    except Exception as e:
        print(f"⚠️  Could not initialize Vertex AI: {e}")
    
    print("\n✅ Test environment ready!\n")


def demo_natural_language_commands():
    """Demo: Natural language command processing."""
    print_section("🤖 QUALITY GUARDIAN AGENT - Natural Language Demo")
    
    print("This demo shows the REAL orchestration layer:")
    print("  ✓ Natural language → Gemini → Tool execution")
    print("  ✓ RAG Corpus integration (persistent storage)")
    print("  ✓ Bootstrap → Sync → Query workflow\n")
    
    # Get test repo name
    test_repo = get_test_repo_name()
    
    # Initialize agent (AFTER corpus cleanup, so it creates fresh corpus)
    print("Initializing Quality Guardian Agent...")
    agent = QualityGuardianAgentV2()
    print("✅ Agent ready!\n")
    
    # Test 1: Bootstrap with natural language
    print_section("TEST 1: Bootstrap Command (Natural Language)")
    
    command1 = f"Bootstrap {test_repo}"
    print(f"🗣️  User: '{command1}'")
    print()
    
    response1 = agent.process_command(command1)
    print(f"\n🤖 Agent: {response1}\n")
    
    # Test 2: Sync command
    print_section("TEST 2: Sync Command (Check for New Commits)")
    
    command2 = f"Sync {test_repo}"
    print(f"🗣️  User: '{command2}'")
    print()
    
    response2 = agent.process_command(command2)
    print(f"\n🤖 Agent: {response2}\n")
    
    # Test 3: Query trends
    print_section("TEST 3: Query Command (Quality Trends)")
    
    command3 = f"Show quality trends for {test_repo}"
    print(f"🗣️  User: '{command3}'")
    print()
    
    response3 = agent.process_command(command3)
    print(f"\n🤖 Agent: {response3}\n")
    
    # Check if query actually worked
    if "error" in response3.lower() or "failed" in response3.lower():
        print("❌ Query command FAILED!")
        print(f"Response: {response3}")
        raise RuntimeError("Query command failed - see output above")
    else:
        print("✅ Query command succeeded")
    
    # Test 4: Unknown command
    print_section("TEST 4: Unknown Command (Help Text)")
    
    command4 = "What can you do?"
    print(f"🗣️  User: '{command4}'")
    print()
    
    response4 = agent.process_command(command4)
    print(f"\n🤖 Agent:\n{response4}\n")


def demo_direct_tool_access():
    """Demo: Direct tool function calls (for testing)."""
    print_section("🔧 DIRECT TOOL ACCESS - For Debugging")
    
    print("These are the same tools Gemini calls, but accessed directly:\n")
    
    agent = QualityGuardianAgentV2()
    test_repo = get_test_repo_name()
    
    # Bootstrap with explicit parameters
    print("Testing bootstrap_repository() with explicit params...")
    result = agent.bootstrap_repository(
        repo_identifier=test_repo,
        strategy="recent",
        count=3  # Small sample for demo
    )
    
    print(f"\n📊 Result:")
    print(f"   Status: {result['status']}")
    print(f"   Commits: {result.get('commits_analyzed', 0)}")
    print(f"   Quality: {result.get('avg_quality_score', 0):.1f}/100")
    print(f"   Issues: {result.get('total_issues', 0)}")
    print(f"   Message: {result['message']}\n")


def interactive_mode():
    """Interactive mode: chat with the agent."""
    print_section("💬 INTERACTIVE MODE - Chat with Quality Guardian")
    
    print("Type commands in natural language. Examples:")
    print("  - Bootstrap facebook/react")
    print("  - Sync myorg/myrepo")
    print("  - Show quality trends for myrepo")
    print("  - Type 'quit' to exit\n")
    
    agent = QualityGuardianAgentV2()
    
    while True:
        try:
            user_input = input("🗣️  You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break
            
            print()
            response = agent.process_command(user_input)
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
    print("║" + "  QUALITY GUARDIAN AGENT v2 - Orchestration Layer Demo".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Progress: ~40% (Agent orchestrates backend tools!)".center(78) + "║")
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
        print("  2. Direct Tool Access (debugging)")
        print("  3. Interactive Mode (chat with agent)")
        print("  4. Run All\n")
        choice = input("Enter choice (1-4): ").strip()
    
    try:
        
        if choice == "1":
            demo_natural_language_commands()
        elif choice == "2":
            demo_direct_tool_access()
        elif choice == "3":
            interactive_mode()
        elif choice == "4":
            demo_natural_language_commands()
            demo_direct_tool_access()
            print("\nWant to try interactive mode? (y/n): ", end="")
            if input().strip().lower() == "y":
                interactive_mode()
        else:
            print("Invalid choice. Running natural language demo...\n")
            demo_natural_language_commands()
        
        print("\n" + "=" * 80)
        print("  ✅ Demo Complete!")
        print("=" * 80)
        print("\nWhat we demonstrated:")
        print("  ✓ Natural language command parsing")
        print("  ✓ Agent orchestrates GitHubConnector + AuditEngine")
        print("  ✓ RAG Corpus stores audit history")
        print("  ✓ Bootstrap → Sync → Query workflow")
        print("\nNext steps:")
        print("  - Add proper Gemini Agent with tool declarations")
        print("  - Implement Query Agent for trend analysis")
        print("  - Add multi-agent coordination\n")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
