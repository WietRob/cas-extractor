"""
AST-normalized fingerprinting for Python symbols.
"""

import ast
import hashlib
import textwrap
from typing import Optional


class _ASTNormalizer(ast.NodeTransformer):
    def __init__(self, strip_docstrings: bool = True, normalize_literals: bool = False):
        self.strip_docstrings = strip_docstrings
        self.normalize_literals = normalize_literals
        self._is_first_expr = True

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self._is_first_expr = True
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        self._is_first_expr = True
        self.generic_visit(node)
        return node

    def visit_Expr(self, node: ast.Expr) -> Optional[ast.Expr]:
        if (
            self.strip_docstrings
            and self._is_first_expr
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            self._is_first_expr = False
            return None
        self._is_first_expr = False
        self.generic_visit(node)
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        if self.normalize_literals:
            if isinstance(node.value, str):
                node.value = "__STR__"
            elif isinstance(node.value, (int, float, complex)):
                node.value = 0
        return node


def fingerprint_ast(
    source: str,
    *,
    strip_docstrings: bool = True,
    normalize_literals: bool = False,
) -> str:
    dedented = textwrap.dedent(source)
    try:
        tree = ast.parse(dedented)
    except SyntaxError:
        return hashlib.sha256(dedented.encode("utf-8")).hexdigest()

    normalizer = _ASTNormalizer(
        strip_docstrings=strip_docstrings,
        normalize_literals=normalize_literals,
    )
    tree = normalizer.visit(tree)
    ast.fix_missing_locations(tree)

    dumped = ast.dump(tree, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def fingerprint_module(source: str) -> str:
    return fingerprint_ast(source, strip_docstrings=True, normalize_literals=False)
