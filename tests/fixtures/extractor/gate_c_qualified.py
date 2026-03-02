"""
Gate C: qualified_attr Resolution

Tests that module.func() calls are resolved via:
- Direct imports
- Import aliases
- From imports
"""

import ast
import json as json_module
from os import path


def main():
    # qualified_attr should resolve to ast.walk
    ast.walk(ast.parse("x"))

    # qualified_attr should resolve to json_module.dumps
    json_module.dumps({"key": "value"})

    # qualified_attr should resolve to path.join
    path.join("a", "b")
