"""Tests for dependency analyzer."""

import pytest
from tools.dependency_analyzer import (
    analyze_dependencies,
    detect_breaking_changes,
    analyze_impact,
    format_impact_report
)


def test_analyze_dependencies_simple():
    """Test basic dependency analysis."""
    code = """
import os
import sys
from pathlib import Path

def public_function():
    pass

def _private_function():
    pass

class PublicClass:
    pass
"""
    
    result = analyze_dependencies(code, "test.py")
    
    assert "os" in result.imports
    assert "sys" in result.imports
    assert "pathlib" in result.imports
    assert "function:public_function" in result.exports
    assert "function:_private_function" not in result.exports
    assert "class:PublicClass" in result.exports


def test_analyze_dependencies_relative_imports():
    """Test handling of relative imports."""
    code = """
from . import utils
from ..models import User
import requests
"""
    
    result = analyze_dependencies(code, "app/module.py")
    
    # Relative imports should not be in external_deps
    assert "requests" in result.external_deps
    assert "utils" not in result.external_deps
    assert "models" not in result.external_deps


def test_detect_breaking_changes_removed_function():
    """Test detection of removed functions."""
    old_code = """
def public_api():
    pass

def another_function():
    pass
"""
    
    new_code = """
def another_function():
    pass
"""
    
    changes = detect_breaking_changes(old_code, new_code, "test.py")
    
    assert len(changes) == 1
    assert "Removed public function: public_api" in changes


def test_detect_breaking_changes_signature_change():
    """Test detection of signature changes."""
    old_code = """
def api_function(arg1, arg2):
    pass
"""
    
    new_code = """
def api_function(arg1, arg2, arg3):
    pass
"""
    
    changes = detect_breaking_changes(old_code, new_code, "test.py")
    
    assert len(changes) == 1
    assert "Changed function signature: api_function" in changes[0]
    assert "2 → 3 args" in changes[0]


def test_detect_breaking_changes_no_changes():
    """Test that identical code produces no breaking changes."""
    code = """
def stable_api(arg1, arg2):
    return arg1 + arg2
"""
    
    changes = detect_breaking_changes(code, code, "test.py")
    
    assert len(changes) == 0


def test_analyze_impact_low_risk(tmp_path):
    """Test low-risk impact analysis."""
    # Create simple Python file
    test_file = tmp_path / "module.py"
    test_file.write_text("""
def helper():
    pass
""")
    
    impact = analyze_impact(
        repo_path=str(tmp_path),
        changed_files=["module.py"]
    )
    
    assert impact.risk_level == "low"
    assert "module.py" in impact.changed_modules


def test_analyze_impact_high_risk_with_breaking_changes(tmp_path):
    """Test high-risk impact when breaking changes detected."""
    test_file = tmp_path / "api.py"
    test_file.write_text("""
def new_api(arg1, arg2, arg3):
    pass
""")
    
    old_versions = {
        "api.py": """
def new_api(arg1):
    pass
"""
    }
    
    impact = analyze_impact(
        repo_path=str(tmp_path),
        changed_files=["api.py"],
        old_versions=old_versions
    )
    
    assert impact.risk_level == "high"
    assert len(impact.breaking_changes) > 0


def test_format_impact_report():
    """Test impact report formatting."""
    from tools.dependency_analyzer import ImpactAnalysis
    
    impact = ImpactAnalysis(
        changed_modules=["app/module1.py", "app/module2.py"],
        affected_modules=["tests/test_module1.py"],
        breaking_changes=["Removed public function: old_api"],
        risk_level="high"
    )
    
    report = format_impact_report(impact)
    
    assert "Risk Level: HIGH" in report
    assert "Changed Modules: 2" in report
    assert "app/module1.py" in report
    assert "Breaking Changes Detected: 1" in report
    assert "Removed public function: old_api" in report


def test_analyze_dependencies_invalid_syntax():
    """Test handling of invalid Python syntax."""
    code = """
def broken(
    # Missing closing parenthesis
"""
    
    with pytest.raises(ValueError, match="Invalid Python syntax"):
        analyze_dependencies(code, "broken.py")


def test_detect_breaking_changes_syntax_error():
    """Test handling of syntax errors in breaking change detection."""
    old_code = "def valid(): pass"
    new_code = "def broken("
    
    changes = detect_breaking_changes(old_code, new_code, "test.py")
    
    assert "Syntax error" in changes[0]
