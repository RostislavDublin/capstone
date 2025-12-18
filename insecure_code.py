"""Intentionally insecure code for testing."""
import subprocess
import pickle
import os


def run_command(cmd):
    """Shell injection vulnerability."""
    return subprocess.call(cmd, shell=True)


def deserialize(data):
    """Unsafe deserialization."""
    return pickle.loads(data)


def super_complex_function(x, y, z, a, b):
    """Extremely complex function."""
    if x > 0:
        if y > 0:
            if z > 0:
                if a > 0:
                    if b > 0:
                        if x > y:
                            if y > z:
                                if z > a:
                                    if a > b:
                                        return x + y + z + a + b
                                    else:
                                        return x - y
                                else:
                                    return y - z
                            else:
                                return z - a
                        else:
                            return a - b
                    else:
                        return x * y
                else:
                    return y * z
            else:
                return z * a
        else:
            return a * b
    return 0
