"""Memory Bank implementation for code review system.

This module provides memory capabilities for the code review system:
- Store review patterns (common issues that recur)
- Store team standards (coding conventions)
- Store author preferences (individual developer patterns)
- Retrieve relevant memories during code review
- Update memories based on review outcomes

Uses in-memory storage that persists for the lifetime of the MemoryBank instance.
In production, this would be backed by a database or persistent storage.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib

from models import ReviewPattern, TeamStandard, IssueType


class MemoryBank:
    """Memory Bank for storing and retrieving code review patterns."""
    
    def __init__(self):
        """Initialize Memory Bank with in-memory storage."""
        self.storage: Dict[str, Dict] = {}
    
    def store_review_pattern(
        self,
        issue_type: IssueType,
        description: str,
        code_example: str,
        repo: Optional[str] = None
    ) -> str:
        """Store a review pattern in memory.
        
        Args:
            issue_type: Type of issue (SECURITY, COMPLEXITY, etc.)
            description: Pattern description
            code_example: Example code that matches this pattern
            repo: Optional repository scope
            
        Returns:
            Pattern ID
        """
        # Generate pattern ID
        pattern_id = self._generate_pattern_id(issue_type, description)
        
        # Check if pattern already exists
        existing = self._get_pattern(pattern_id)
        
        if existing:
            # Update existing pattern
            existing["frequency"] += 1
            existing["last_seen"] = datetime.now().isoformat()
            existing["examples"].append(code_example)
            # Keep only last 5 examples
            existing["examples"] = existing["examples"][-5:]
        else:
            # Create new pattern
            existing = {
                "pattern_id": pattern_id,
                "issue_type": issue_type.value,
                "description": description,
                "examples": [code_example],
                "frequency": 1,
                "acceptance_rate": 0.0,
                "last_seen": datetime.now().isoformat(),
                "repo": repo
            }
        
        # Store in session
        self._store_item(f"pattern:{pattern_id}", existing)
        
        return pattern_id
    
    def store_team_standard(
        self,
        category: str,
        rule: str,
        examples: List[str],
        repo: Optional[str] = None
    ) -> str:
        """Store a team coding standard.
        
        Args:
            category: Standard category (naming, architecture, etc.)
            rule: The standard rule
            examples: Code examples
            repo: Optional repository scope
            
        Returns:
            Standard ID
        """
        # Generate standard ID
        standard_id = self._generate_standard_id(category, rule)
        
        # Check if standard already exists
        existing = self._get_standard(standard_id)
        
        if existing:
            # Update existing standard
            existing["examples"].extend(examples)
            existing["examples"] = list(set(existing["examples"]))  # Deduplicate
            existing["violations_count"] = existing.get("violations_count", 0)
        else:
            # Create new standard
            existing = {
                "standard_id": standard_id,
                "category": category,
                "rule": rule,
                "examples": examples,
                "violations_count": 0,
                "repo": repo,
                "created_at": datetime.now().isoformat()
            }
        
        # Store in session
        self._store_item(f"standard:{standard_id}", existing)
        
        return standard_id
    
    def record_violation(self, standard_id: str):
        """Record a violation of a team standard.
        
        Args:
            standard_id: Standard that was violated
        """
        standard = self._get_standard(standard_id)
        if standard:
            standard["violations_count"] = standard.get("violations_count", 0) + 1
            self._store_item(f"standard:{standard_id}", standard)
    
    def update_pattern_acceptance(self, pattern_id: str, accepted: bool):
        """Update pattern acceptance rate based on review outcome.
        
        Args:
            pattern_id: Pattern to update
            accepted: Whether the pattern-based suggestion was accepted
        """
        pattern = self._get_pattern(pattern_id)
        if pattern:
            frequency = pattern["frequency"]
            current_rate = pattern.get("acceptance_rate", 0.0)
            
            # Calculate new acceptance rate
            # (current_rate * (frequency - 1) + (1 if accepted else 0)) / frequency
            new_rate = (current_rate * (frequency - 1) + (1.0 if accepted else 0.0)) / frequency
            pattern["acceptance_rate"] = new_rate
            
            self._store_item(f"pattern:{pattern_id}", pattern)
    
    def find_similar_patterns(
        self,
        issue_type: IssueType,
        min_frequency: int = 2,
        repo: Optional[str] = None
    ) -> List[ReviewPattern]:
        """Find similar patterns from memory.
        
        Args:
            issue_type: Type of issue to search for
            min_frequency: Minimum pattern frequency to return
            repo: Optional repository scope
            
        Returns:
            List of matching ReviewPattern objects
        """
        # Get all patterns for this issue type
        all_patterns = self._get_all_patterns()
        
        matching = []
        for pattern_data in all_patterns:
            # Filter by issue type
            if pattern_data.get("issue_type") != issue_type.value:
                continue
            
            # Filter by frequency
            if pattern_data.get("frequency", 0) < min_frequency:
                continue
            
            # Filter by repo if specified
            if repo and pattern_data.get("repo") and pattern_data["repo"] != repo:
                continue
            
            # Convert to ReviewPattern
            pattern = ReviewPattern(
                pattern_id=pattern_data["pattern_id"],
                issue_type=IssueType(pattern_data["issue_type"]),
                description=pattern_data["description"],
                example=pattern_data["examples"][0] if pattern_data["examples"] else "",
                frequency=pattern_data["frequency"],
                acceptance_rate=pattern_data.get("acceptance_rate", 0.0),
                last_seen=datetime.fromisoformat(pattern_data["last_seen"])
            )
            matching.append(pattern)
        
        # Sort by frequency and acceptance rate
        matching.sort(
            key=lambda p: (p.frequency, p.acceptance_rate),
            reverse=True
        )
        
        return matching[:5]  # Return top 5
    
    def get_team_standards(
        self,
        category: Optional[str] = None,
        repo: Optional[str] = None
    ) -> List[TeamStandard]:
        """Get team coding standards.
        
        Args:
            category: Optional category filter
            repo: Optional repository scope
            
        Returns:
            List of TeamStandard objects
        """
        all_standards = self._get_all_standards()
        
        matching = []
        for standard_data in all_standards:
            # Filter by category
            if category and standard_data.get("category") != category:
                continue
            
            # Filter by repo
            if repo and standard_data.get("repo") and standard_data["repo"] != repo:
                continue
            
            # Convert to TeamStandard
            standard = TeamStandard(
                standard_id=standard_data["standard_id"],
                category=standard_data["category"],
                rule=standard_data["rule"],
                examples=standard_data.get("examples", []),
                violations_count=standard_data.get("violations_count", 0)
            )
            matching.append(standard)
        
        return matching
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory bank statistics.
        
        Returns:
            Dict with statistics about stored memories
        """
        patterns = self._get_all_patterns()
        standards = self._get_all_standards()
        
        # Calculate pattern stats
        pattern_stats = {
            "total_patterns": len(patterns),
            "by_type": {},
            "avg_frequency": 0.0,
            "avg_acceptance": 0.0
        }
        
        if patterns:
            total_freq = sum(p.get("frequency", 0) for p in patterns)
            total_acceptance = sum(p.get("acceptance_rate", 0.0) for p in patterns)
            pattern_stats["avg_frequency"] = total_freq / len(patterns)
            pattern_stats["avg_acceptance"] = total_acceptance / len(patterns)
            
            # Count by type
            for p in patterns:
                issue_type = p.get("issue_type", "unknown")
                pattern_stats["by_type"][issue_type] = pattern_stats["by_type"].get(issue_type, 0) + 1
        
        # Calculate standard stats
        standard_stats = {
            "total_standards": len(standards),
            "by_category": {},
            "total_violations": sum(s.get("violations_count", 0) for s in standards)
        }
        
        for s in standards:
            category = s.get("category", "unknown")
            standard_stats["by_category"][category] = standard_stats["by_category"].get(category, 0) + 1
        
        return {
            "patterns": pattern_stats,
            "standards": standard_stats
        }
    
    def clear_old_patterns(self, days: int = 90):
        """Clear patterns not seen in the specified number of days.
        
        Args:
            days: Number of days threshold
        """
        cutoff = datetime.now() - timedelta(days=days)
        patterns = self._get_all_patterns()
        
        for pattern in patterns:
            last_seen = datetime.fromisoformat(pattern["last_seen"])
            if last_seen < cutoff:
                pattern_id = pattern["pattern_id"]
                self._delete_item(f"pattern:{pattern_id}")
    
    # Private helper methods
    
    def _generate_pattern_id(self, issue_type: IssueType, description: str) -> str:
        """Generate unique pattern ID."""
        content = f"{issue_type.value}:{description}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_standard_id(self, category: str, rule: str) -> str:
        """Generate unique standard ID."""
        content = f"{category}:{rule}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _store_item(self, key: str, data: Dict):
        """Store item in memory."""
        self.storage[key] = data.copy()
    
    def _get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """Get pattern from memory."""
        key = f"pattern:{pattern_id}"
        return self.storage.get(key)
    
    def _get_standard(self, standard_id: str) -> Optional[Dict]:
        """Get standard from memory."""
        key = f"standard:{standard_id}"
        return self.storage.get(key)
    
    def _get_all_patterns(self) -> List[Dict]:
        """Get all patterns from memory."""
        patterns = []
        for key, value in self.storage.items():
            if key.startswith("pattern:"):
                patterns.append(value)
        return patterns
    
    def _get_all_standards(self) -> List[Dict]:
        """Get all standards from memory."""
        standards = []
        for key, value in self.storage.items():
            if key.startswith("standard:"):
                standards.append(value)
        return standards
    
    def _delete_item(self, key: str):
        """Delete item from memory."""
        if key in self.storage:
            del self.storage[key]
