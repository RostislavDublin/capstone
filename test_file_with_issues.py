"""Test file with intentional security and complexity issues."""
import subprocess
import pickle


def execute_command(user_input):
    """Execute shell command - SECURITY ISSUE."""
    # B602: shell injection vulnerability
    result = subprocess.call(user_input, shell=True)
    return result


def load_data(filename):
    """Load pickled data - SECURITY ISSUE."""
    # B301: pickle usage
    with open(filename, 'rb') as f:
        return pickle.load(f)


def complex_function(a, b, c, d, e):
    """Very complex function - COMPLEXITY ISSUE."""
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if a > b:
                            if b > c:
                                if c > d:
                                    if d > e:
                                        return a + b + c + d + e
                                    else:
                                        return a - b
                                else:
                                    return b - c
                            else:
                                return c - d
                        else:
                            return d - e
                    else:
                        return a * b
                else:
                    return b * c
            else:
                return c * d
        else:
            return d * e
    else:
        return 0
