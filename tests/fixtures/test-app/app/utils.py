"""Utility functions with high cyclomatic complexity.

COMPLEXITY ISSUES:
- Function exceeds complexity threshold
- Deep nesting (5+ levels)
- Multiple responsibilities
- No helper function extraction
"""

import json
from typing import Any, Dict, List, Optional


def process_data(data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """⚠️ HIGH COMPLEXITY: Cyclomatic complexity = 18
    
    This function does too many things:
    - Validation
    - Transformation
    - Filtering
    - Aggregation
    - Error handling (sort of)
    
    Should be split into smaller functions.
    """
    result = {}
    
    # Level 1 nesting
    if data is not None:
        # Level 2 nesting
        if "items" in data:
            items = data["items"]
            processed_items = []
            
            # Level 3 nesting
            for item in items:
                # Level 4 nesting
                if item.get("active", False):
                    # Level 5 nesting - TOO DEEP!
                    if "price" in item:
                        if item["price"] > 0:
                            if options.get("apply_discount", False):
                                if "discount_rate" in options:
                                    item["price"] = item["price"] * (1 - options["discount_rate"])
                                else:
                                    item["price"] = item["price"] * 0.9
                            processed_items.append(item)
                        else:
                            if options.get("include_free", False):
                                processed_items.append(item)
                    elif "cost" in item:
                        if options.get("use_cost_fallback", True):
                            item["price"] = item["cost"] * 1.2
                            processed_items.append(item)
            
            result["items"] = processed_items
        
        # More complexity branches
        if "metadata" in data:
            metadata = data["metadata"]
            if metadata.get("version", 1) >= 2:
                if "tags" in metadata:
                    filtered_tags = []
                    for tag in metadata["tags"]:
                        if tag.startswith("prod-"):
                            filtered_tags.append(tag)
                        elif tag.startswith("test-"):
                            if options.get("include_test_tags", False):
                                filtered_tags.append(tag)
                    result["tags"] = filtered_tags
        
        # Even more branches
        if options.get("compute_stats", False):
            if "items" in result:
                total = sum(item.get("price", 0) for item in result["items"])
                count = len(result["items"])
                if count > 0:
                    result["stats"] = {
                        "total": total,
                        "average": total / count,
                        "count": count
                    }
                else:
                    result["stats"] = {"total": 0, "average": 0, "count": 0}
    else:
        result = {"error": "No data provided"}
    
    return result


def validate_input_data(data: Any) -> bool:
    """💡 MEDIUM: Unnecessary complexity, could use schema validation."""
    if data is None:
        return False
    if not isinstance(data, dict):
        return False
    if "items" not in data:
        return False
    if not isinstance(data["items"], list):
        return False
    for item in data["items"]:
        if not isinstance(item, dict):
            return False
        if "active" in item and not isinstance(item["active"], bool):
            return False
    return True


# 💡 STYLE: Inconsistent naming - should be snake_case
def calculateTotalPrice(items: List[Dict]) -> float:
    """Mixed naming convention."""
    totalPrice = 0.0
    for item in items:
        if "price" in item:
            totalPrice += item["price"]
    return totalPrice
