#!/usr/bin/env python3
"""Demonstration of Memory Bank capabilities.

This script shows how the Memory Bank:
1. Stores review patterns from code reviews
2. Tracks pattern frequency and acceptance rates
3. Stores team coding standards
4. Recalls similar patterns during reviews
5. Provides statistics about learned patterns

It demonstrates the learning and pattern recognition capabilities
that enhance code reviews over time.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory.review_memory import MemoryBank
from models import IssueType


def print_separator(title: str = ""):
    """Print section separator."""
    if title:
        print()
        print("=" * 80)
        print(title.center(80))
        print("=" * 80)
    else:
        print("-" * 80)


def main():
    """Run Memory Bank demonstration."""
    print_separator("MEMORY BANK DEMONSTRATION")
    print()
    print("This demo shows how the Memory Bank learns from code reviews")
    print("and provides pattern recognition for future reviews.")
    print()
    
    # Initialize Memory Bank
    print("Initializing Memory Bank...")
    memory = MemoryBank()
    print("✓ Memory Bank initialized")
    print()
    
    # Scenario 1: Storing review patterns
    print_separator("SCENARIO 1: Learning from Code Reviews")
    print()
    print("Review 1: Found SQL injection in PR #123")
    pattern_id1 = memory.store_review_pattern(
        issue_type=IssueType.SECURITY,
        description="SQL injection - string interpolation in query",
        code_example="query = f'SELECT * FROM users WHERE id={user_id}'",
        repo="acme/web-app"
    )
    print(f"   ✓ Pattern stored: {pattern_id1}")
    memory.update_pattern_acceptance(pattern_id1, accepted=True)
    print("   ✓ Developer fixed the issue (accepted)")
    print()
    
    print("Review 2: Found similar SQL injection in PR #156")
    pattern_id2 = memory.store_review_pattern(
        issue_type=IssueType.SECURITY,
        description="SQL injection - string interpolation in query",
        code_example="query = \"DELETE FROM sessions WHERE user_id = %s\" % user_id",
        repo="acme/web-app"
    )
    print(f"   ✓ Same pattern detected: {pattern_id2 == pattern_id1}")
    print("   ✓ Frequency increased to 2")
    memory.update_pattern_acceptance(pattern_id2, accepted=True)
    print("   ✓ Developer fixed the issue (accepted)")
    print()
    
    print("Review 3: Found yet another SQL injection in PR #189")
    memory.store_review_pattern(
        issue_type=IssueType.SECURITY,
        description="SQL injection - string interpolation in query",
        code_example="query = 'UPDATE users SET name = \"' + name + '\" WHERE id = ' + str(id)",
        repo="acme/web-app"
    )
    print("   ✓ Frequency increased to 3")
    print("   ✓ This is a recurring pattern!")
    print()
    
    # Scenario 2: Recalling similar patterns
    print_separator("SCENARIO 2: Pattern Recognition During Review")
    print()
    print("New PR #205 contains security concerns...")
    print("Checking Memory Bank for similar patterns...")
    print()
    
    patterns = memory.find_similar_patterns(
        issue_type=IssueType.SECURITY,
        min_frequency=2
    )
    
    if patterns:
        print(f"🔍 Found {len(patterns)} similar pattern(s):")
        print()
        for i, pattern in enumerate(patterns, 1):
            print(f"{i}. {pattern.description}")
            print(f"   Frequency: {pattern.frequency} times")
            print(f"   Acceptance Rate: {pattern.acceptance_rate * 100:.0f}%")
            print(f"   Last Seen: {pattern.last_seen.strftime('%Y-%m-%d')}")
            print(f"   Example: {pattern.example[:60]}...")
            print()
        
        print("💡 Recommendation: High-confidence security issue detected")
        print("   Developers in this repo consistently make this mistake")
        print("   Consider adding automated check or documentation")
    print()
    
    # Scenario 3: Team Standards
    print_separator("SCENARIO 3: Team Coding Standards")
    print()
    print("Storing team standards...")
    
    std1_id = memory.store_team_standard(
        category="security",
        rule="Always use parameterized queries for database operations",
        examples=[
            "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
            "session.query(User).filter(User.id == user_id)"
        ],
        repo="acme/web-app"
    )
    print(f"   ✓ Standard stored: {std1_id}")
    
    memory.store_team_standard(
        category="naming",
        rule="Use snake_case for variables and functions",
        examples=["user_id", "calculate_total", "get_user_by_email"],
        repo="acme/web-app"
    )
    print("   ✓ Naming standard stored")
    
    memory.store_team_standard(
        category="testing",
        rule="All public functions must have unit tests",
        examples=["test_calculate_total", "test_get_user_by_email"],
        repo="acme/web-app"
    )
    print("   ✓ Testing standard stored")
    print()
    
    # Record violations
    print("Recording standard violations from reviews...")
    memory.record_violation(std1_id)
    memory.record_violation(std1_id)
    memory.record_violation(std1_id)
    print(f"   ✓ Security standard violated 3 times")
    print()
    
    # Get standards
    print("Retrieving team standards...")
    standards = memory.get_team_standards()
    print(f"   Found {len(standards)} team standards:")
    print()
    for std in standards:
        print(f"   • {std.category.upper()}: {std.rule}")
        if std.violations_count > 0:
            print(f"     ⚠️  Violated {std.violations_count} times")
    print()
    
    # Scenario 4: Different issue types
    print_separator("SCENARIO 4: Multiple Issue Types")
    print()
    print("Storing patterns for different issue types...")
    
    memory.store_review_pattern(
        issue_type=IssueType.COMPLEXITY,
        description="Function with cyclomatic complexity > 20",
        code_example="def process_user_action(...): # many nested if/else",
        repo="acme/web-app"
    )
    memory.store_review_pattern(
        issue_type=IssueType.COMPLEXITY,
        description="Function with cyclomatic complexity > 20",
        code_example="def handle_request(...): # deeply nested logic",
        repo="acme/web-app"
    )
    print("   ✓ Complexity patterns stored")
    
    memory.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Potential null pointer access",
        code_example="return user.name  # user might be None",
        repo="acme/web-app"
    )
    print("   ✓ Bug pattern stored")
    print()
    
    # Statistics
    print_separator("MEMORY BANK STATISTICS")
    print()
    stats = memory.get_statistics()
    
    print(f"Patterns:")
    print(f"   Total: {stats['patterns']['total_patterns']}")
    print(f"   Average Frequency: {stats['patterns']['avg_frequency']:.1f}")
    print(f"   Average Acceptance: {stats['patterns']['avg_acceptance'] * 100:.1f}%")
    print()
    print(f"   By Type:")
    for issue_type, count in stats['patterns']['by_type'].items():
        print(f"      {issue_type}: {count}")
    print()
    
    print(f"Standards:")
    print(f"   Total: {stats['standards']['total_standards']}")
    print(f"   Total Violations: {stats['standards']['total_violations']}")
    print()
    print(f"   By Category:")
    for category, count in stats['standards']['by_category'].items():
        print(f"      {category}: {count}")
    print()
    
    # Scenario 5: Pattern-based recommendations
    print_separator("SCENARIO 5: Smart Recommendations")
    print()
    print("When reviewing PR #250 with security concerns:")
    print()
    
    security_patterns = memory.find_similar_patterns(
        issue_type=IssueType.SECURITY,
        min_frequency=2
    )
    
    if security_patterns:
        top_pattern = security_patterns[0]
        print(f"🤖 AI-Enhanced Recommendation:")
        print(f"   \"This looks like: {top_pattern.description}\"")
        print(f"   \"I've seen this {top_pattern.frequency} times before in this repo\"")
        print(f"   \"Developers accepted this review {top_pattern.acceptance_rate * 100:.0f}% of the time\"")
        print(f"   \"Suggest using parameterized queries (team standard)\"")
    print()
    
    # Summary
    print_separator("KEY BENEFITS")
    print()
    print("✅ Pattern Learning: Automatically learns from each review")
    print("✅ Smart Recall: Finds similar issues based on patterns")
    print("✅ Team Memory: Stores and tracks coding standards")
    print("✅ Trend Analysis: Tracks violation frequency and acceptance")
    print("✅ Context-Aware: Provides repo-specific recommendations")
    print()
    
    print_separator("DEMONSTRATION COMPLETE")
    print()
    print("The Memory Bank has learned:")
    print(f"  • {stats['patterns']['total_patterns']} review patterns")
    print(f"  • {stats['standards']['total_standards']} team standards")
    print(f"  • Recognition of recurring issues")
    print(f"  • High-confidence recommendations")
    print()
    print("Next: Integrate with Context Agent for memory-enhanced reviews")
    print()


if __name__ == "__main__":
    main()
