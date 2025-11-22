"""Unit tests for security scanner tool."""

import pytest
from lib.security_scanner import (
    detect_security_issues,
    format_security_report,
    SecurityIssue,
    SecurityScanResult
)


def test_detect_sql_injection():
    """Test detection of SQL injection vulnerability."""
    code = '''
def query_database(user_id):
    connection = get_db_connection()
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchall()
'''
    
    result = detect_security_issues(code, "python")
    
    assert result.total_issues > 0
    # Should detect SQL injection (B608 - hardcoded SQL expressions)
    assert any(issue.test_id == "B608" for issue in result.issues)


def test_detect_hardcoded_password():
    """Test detection of hardcoded password."""
    code = '''
def connect_to_api():
    password = "super_secret_123"
    api_key = "hardcoded_api_key_456"
    return authenticate(password, api_key)
'''
    
    result = detect_security_issues(code, "python")
    
    assert result.total_issues > 0
    # Should detect hardcoded password (B105)
    assert any(issue.test_id == "B105" for issue in result.issues)


def test_detect_shell_injection():
    """Test detection of shell injection via subprocess."""
    code = '''
import subprocess

def run_command(user_input):
    subprocess.call("ls " + user_input, shell=True)
'''
    
    result = detect_security_issues(code, "python")
    
    assert result.total_issues > 0
    # Should detect shell injection (B602, B605, or B607)
    assert result.high_severity_count > 0


def test_detect_insecure_ssl():
    """Test detection of SSL verification disabled."""
    code = '''
import requests

def fetch_data(url):
    response = requests.get(url, verify=False)
    return response.json()
'''
    
    result = detect_security_issues(code, "python")
    
    assert result.total_issues > 0
    # Should detect insecure SSL (B501)


def test_detect_pickle_usage():
    """Test detection of unsafe pickle usage."""
    code = '''
import pickle

def load_data(file_path):
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    return data
'''
    
    result = detect_security_issues(code, "python")
    
    assert result.total_issues > 0
    # Should detect unsafe deserialization (B301)


def test_clean_code_no_issues():
    """Test that clean code returns no issues."""
    code = '''
def safe_function(x, y):
    """A safe function with no security issues."""
    result = x + y
    return result

def another_safe_function():
    data = [1, 2, 3]
    return sum(data)
'''
    
    result = detect_security_issues(code, "python")
    
    assert result.total_issues == 0
    assert result.high_severity_count == 0
    assert result.medium_severity_count == 0
    assert result.low_severity_count == 0


def test_empty_code_raises_error():
    """Test that empty code raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        detect_security_issues("", "python")
    
    with pytest.raises(ValueError, match="cannot be empty"):
        detect_security_issues("   \n  \n", "python")


def test_unsupported_language_raises_error():
    """Test that unsupported language raises ValueError."""
    with pytest.raises(ValueError, match="not supported"):
        detect_security_issues("console.log('test');", "javascript")


def test_severity_counts():
    """Test that severity counts are accurate."""
    code = '''
import pickle
import subprocess

password = "hardcoded_password"

def run_cmd(user_input):
    subprocess.call("ls " + user_input, shell=True)

def load_pickle(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)
'''
    
    result = detect_security_issues(code, "python")
    
    assert result.total_issues > 0
    assert result.total_issues == (
        result.high_severity_count + 
        result.medium_severity_count + 
        result.low_severity_count
    )
    assert len(result.issues) == result.total_issues


def test_security_issue_attributes():
    """Test that SecurityIssue has all required attributes."""
    code = '''
import subprocess
subprocess.call("ls", shell=True)
'''
    
    result = detect_security_issues(code, "python")
    
    assert result.total_issues > 0
    issue = result.issues[0]
    
    assert hasattr(issue, 'issue_severity')
    assert hasattr(issue, 'issue_confidence')
    assert hasattr(issue, 'issue_text')
    assert hasattr(issue, 'test_id')
    assert hasattr(issue, 'test_name')
    assert hasattr(issue, 'line_number')
    assert hasattr(issue, 'line_range')
    assert hasattr(issue, 'code')
    
    assert issue.issue_severity in ["HIGH", "MEDIUM", "LOW"]
    assert issue.issue_confidence in ["HIGH", "MEDIUM", "LOW"]
    assert isinstance(issue.line_number, int)
    assert isinstance(issue.line_range, list)


def test_format_security_report_no_issues():
    """Test report formatting with no issues."""
    result = SecurityScanResult(
        issues=[],
        high_severity_count=0,
        medium_severity_count=0,
        low_severity_count=0,
        total_issues=0
    )
    
    report = format_security_report(result)
    assert "No security issues detected" in report


def test_format_security_report_with_issues():
    """Test report formatting with issues."""
    issue = SecurityIssue(
        issue_severity="HIGH",
        issue_confidence="HIGH",
        issue_text="Test security issue",
        test_id="B999",
        test_name="test_security_check",
        line_number=5,
        line_range=[5, 6],
        code="subprocess.call('ls', shell=True)",
        cwe_id="CWE-78",
        more_info="https://example.com/security"
    )
    
    result = SecurityScanResult(
        issues=[issue],
        high_severity_count=1,
        medium_severity_count=0,
        low_severity_count=0,
        total_issues=1
    )
    
    report = format_security_report(result)
    
    assert "Total Issues: 1" in report
    assert "High Severity: 1" in report
    assert "B999" in report
    assert "Test security issue" in report
    assert "Line: 5" in report
    assert "CWE-78" in report
