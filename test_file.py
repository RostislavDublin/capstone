"""Test file for integration testing."""


def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b


def calculate_product(a: int, b: int) -> int:
    """Calculate product of two numbers."""
    result = a * b
    return result


class Calculator:
    """Simple calculator class."""
    
    def add(self, x: int, y: int) -> int:
        """Add two numbers."""
        return x + y
    
    def multiply(self, x: int, y: int) -> int:
        """Multiply two numbers."""
        temp = x * y
        return temp
