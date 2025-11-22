#!/usr/bin/env python3
"""Quick integration test runner - run individual agent tests."""

import sys
import subprocess
from pathlib import Path

tests_dir = Path(__file__).parent

tests = {
    "1": ("Bootstrap Agent - Count Parameter", "test_bootstrap_agent.py"),
    "2": ("Query Agent - Date Accuracy", "test_query_agent.py"),
    "3": ("Sync Agent - New Commits", "test_sync_agent.py"),
}

def main():
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("\n🧪 Integration Test Suite\n")
        for key, (name, _) in tests.items():
            print(f"  {key}. {name}")
        print()
        choice = input("Choose test (1-3, or 'all'): ").strip()
    
    if choice == "all":
        for _, (name, script) in tests.items():
            print(f"\n▶️  Running: {name}")
            subprocess.run([sys.executable, tests_dir / script])
    elif choice in tests:
        name, script = tests[choice]
        print(f"\n▶️  Running: {name}")
        subprocess.run([sys.executable, tests_dir / script])
    else:
        print("Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    main()
