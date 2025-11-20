"""Unit tests for Memory Bank."""

import pytest
from datetime import datetime, timedelta

from memory.review_memory import MemoryBank
from models import IssueType, ReviewPattern, TeamStandard


@pytest.fixture
def memory_bank():
    """Create fresh Memory Bank for each test."""
    return MemoryBank()


def test_memory_bank_initialization(memory_bank):
    """Test Memory Bank initializes correctly."""
    assert memory_bank.storage is not None
    assert isinstance(memory_bank.storage, dict)


def test_store_review_pattern(memory_bank):
    """Test storing a review pattern."""
    pattern_id = memory_bank.store_review_pattern(
        issue_type=IssueType.SECURITY,
        description="SQL injection vulnerability",
        code_example="query = f'SELECT * FROM users WHERE id={user_id}'",
        repo="test/repo"
    )
    
    assert pattern_id is not None
    assert isinstance(pattern_id, str)
    assert len(pattern_id) == 16  # MD5 hash truncated to 16 chars


def test_store_duplicate_pattern_increases_frequency(memory_bank):
    """Test storing same pattern multiple times increases frequency."""
    pattern_id1 = memory_bank.store_review_pattern(
        issue_type=IssueType.SECURITY,
        description="SQL injection",
        code_example="query = f'SELECT * FROM users'",
    )
    
    pattern_id2 = memory_bank.store_review_pattern(
        issue_type=IssueType.SECURITY,
        description="SQL injection",
        code_example="query = f'DELETE FROM sessions'",
    )
    
    # Should be the same pattern
    assert pattern_id1 == pattern_id2
    
    # Get pattern and check frequency
    pattern = memory_bank._get_pattern(pattern_id1)
    assert pattern["frequency"] == 2
    assert len(pattern["examples"]) == 2


def test_store_team_standard(memory_bank):
    """Test storing a team standard."""
    standard_id = memory_bank.store_team_standard(
        category="naming",
        rule="Use snake_case for variables",
        examples=["user_id", "total_count"],
        repo="test/repo"
    )
    
    assert standard_id is not None
    assert isinstance(standard_id, str)


def test_record_violation(memory_bank):
    """Test recording standard violations."""
    standard_id = memory_bank.store_team_standard(
        category="security",
        rule="Always use parameterized queries",
        examples=[]
    )
    
    # Record violations
    memory_bank.record_violation(standard_id)
    memory_bank.record_violation(standard_id)
    
    standard = memory_bank._get_standard(standard_id)
    assert standard["violations_count"] == 2


def test_update_pattern_acceptance(memory_bank):
    """Test updating pattern acceptance rate."""
    pattern_id = memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Null pointer issue",
        code_example="user.name"
    )
    
    # First review: accepted
    memory_bank.update_pattern_acceptance(pattern_id, accepted=True)
    pattern = memory_bank._get_pattern(pattern_id)
    assert pattern["acceptance_rate"] == pytest.approx(1.0)
    
    # Store pattern again (frequency = 2)
    memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Null pointer issue",
        code_example="user.email"
    )
    
    # Second review: rejected
    memory_bank.update_pattern_acceptance(pattern_id, accepted=False)
    pattern = memory_bank._get_pattern(pattern_id)
    assert pattern["acceptance_rate"] == pytest.approx(0.5)  # 1 accepted, 1 rejected


def test_find_similar_patterns_by_issue_type(memory_bank):
    """Test finding patterns by issue type."""
    # Store multiple patterns
    memory_bank.store_review_pattern(
        issue_type=IssueType.SECURITY,
        description="SQL injection",
        code_example="query1"
    )
    memory_bank.store_review_pattern(
        issue_type=IssueType.SECURITY,
        description="SQL injection",
        code_example="query2"
    )
    memory_bank.store_review_pattern(
        issue_type=IssueType.COMPLEXITY,
        description="High cyclomatic complexity",
        code_example="complex_function"
    )
    
    # Find security patterns
    patterns = memory_bank.find_similar_patterns(
        issue_type=IssueType.SECURITY,
        min_frequency=2
    )
    
    assert len(patterns) == 1
    assert patterns[0].issue_type == IssueType.SECURITY
    assert patterns[0].frequency == 2


def test_find_patterns_filters_by_frequency(memory_bank):
    """Test pattern filtering by frequency."""
    # Store pattern once
    memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Off-by-one error",
        code_example="range(len(arr))"
    )
    
    # Should not return with min_frequency=2
    patterns = memory_bank.find_similar_patterns(
        issue_type=IssueType.BUG,
        min_frequency=2
    )
    
    assert len(patterns) == 0
    
    # Store again
    memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Off-by-one error",
        code_example="range(len(arr)+1)"
    )
    
    # Now should return
    patterns = memory_bank.find_similar_patterns(
        issue_type=IssueType.BUG,
        min_frequency=2
    )
    
    assert len(patterns) == 1


def test_get_team_standards(memory_bank):
    """Test retrieving team standards."""
    # Store standards
    memory_bank.store_team_standard(
        category="naming",
        rule="Use snake_case",
        examples=[]
    )
    memory_bank.store_team_standard(
        category="security",
        rule="Use parameterized queries",
        examples=[]
    )
    
    # Get all standards
    standards = memory_bank.get_team_standards()
    assert len(standards) == 2
    
    # Get by category
    naming_standards = memory_bank.get_team_standards(category="naming")
    assert len(naming_standards) == 1
    assert naming_standards[0].category == "naming"


def test_get_statistics(memory_bank):
    """Test memory bank statistics."""
    # Store some patterns and standards
    memory_bank.store_review_pattern(
        issue_type=IssueType.SECURITY,
        description="Pattern 1",
        code_example="code1"
    )
    memory_bank.store_review_pattern(
        issue_type=IssueType.COMPLEXITY,
        description="Pattern 2",
        code_example="code2"
    )
    memory_bank.store_team_standard(
        category="naming",
        rule="Rule 1",
        examples=[]
    )
    
    stats = memory_bank.get_statistics()
    
    assert stats["patterns"]["total_patterns"] == 2
    assert "security" in stats["patterns"]["by_type"]
    assert "complexity" in stats["patterns"]["by_type"]
    assert stats["standards"]["total_standards"] == 1
    assert "naming" in stats["standards"]["by_category"]


def test_pattern_returns_review_pattern_objects(memory_bank):
    """Test that find_similar_patterns returns proper ReviewPattern objects."""
    memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Test pattern",
        code_example="test_code"
    )
    memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Test pattern",
        code_example="test_code2"
    )
    
    patterns = memory_bank.find_similar_patterns(
        issue_type=IssueType.BUG,
        min_frequency=1
    )
    
    assert len(patterns) > 0
    assert isinstance(patterns[0], ReviewPattern)
    assert patterns[0].issue_type == IssueType.BUG
    assert isinstance(patterns[0].last_seen, datetime)


def test_standards_return_team_standard_objects(memory_bank):
    """Test that get_team_standards returns proper TeamStandard objects."""
    memory_bank.store_team_standard(
        category="testing",
        rule="All functions must have unit tests",
        examples=["test_function()"]
    )
    
    standards = memory_bank.get_team_standards()
    
    assert len(standards) > 0
    assert isinstance(standards[0], TeamStandard)
    assert standards[0].category == "testing"


def test_pattern_id_consistency(memory_bank):
    """Test that same pattern generates same ID."""
    id1 = memory_bank._generate_pattern_id(
        IssueType.SECURITY,
        "SQL injection"
    )
    id2 = memory_bank._generate_pattern_id(
        IssueType.SECURITY,
        "SQL injection"
    )
    
    assert id1 == id2


def test_standard_id_consistency(memory_bank):
    """Test that same standard generates same ID."""
    id1 = memory_bank._generate_standard_id(
        "naming",
        "Use snake_case"
    )
    id2 = memory_bank._generate_standard_id(
        "naming",
        "Use snake_case"
    )
    
    assert id1 == id2


def test_patterns_sorted_by_frequency_and_acceptance(memory_bank):
    """Test that patterns are sorted by frequency and acceptance rate."""
    # Create patterns with different frequencies
    p1_id = memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Pattern 1",
        code_example="code1"
    )
    
    p2_id = memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Pattern 2",
        code_example="code2"
    )
    memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Pattern 2",
        code_example="code2b"
    )
    memory_bank.store_review_pattern(
        issue_type=IssueType.BUG,
        description="Pattern 2",
        code_example="code2c"
    )
    
    # Update acceptance rates
    memory_bank.update_pattern_acceptance(p1_id, accepted=True)
    memory_bank.update_pattern_acceptance(p2_id, accepted=False)
    
    patterns = memory_bank.find_similar_patterns(
        issue_type=IssueType.BUG,
        min_frequency=1
    )
    
    # Pattern 2 should be first (higher frequency)
    assert patterns[0].frequency == 3
    assert patterns[1].frequency == 1
