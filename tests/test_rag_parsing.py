"""Quick test for RAG query parsing fix."""

import re
import sys
from pathlib import Path

# Sample text from RAG (what we actually get)
sample_text = """commit_sha a660c2c7e3f7fd89563b5af9b151108cff281350
commit_message feat: Add main application module
author Rostislav Dublin
quality_score 87.5
total_issues 12
files_changed 3"""

print("Sample RAG text:")
print(sample_text)
print()

# Test regex parsing
sha_match = re.search(r'commit_sha[:\s]+([a-f0-9]{40})', sample_text)
score_match = re.search(r'quality_score[:\s]+(\d+\.?\d*)', sample_text)

if sha_match and score_match:
    commit_sha = sha_match.group(1)
    quality_score = float(score_match.group(1))
    
    print("✓ Parsed successfully:")
    print(f"  commit_sha: {commit_sha[:7]}")
    print(f"  quality_score: {quality_score}")
else:
    print("❌ Parse failed")
    print(f"  sha_match: {sha_match}")
    print(f"  score_match: {score_match}")
