"""
Python Symbol Extractor — produces py.symbols evidence (E0).

Walks all .py files in a repo, parses AST, extracts:
  - functions (top-level + nested)
  - classes
  - methods
  - module-level variables (optional, v0.1: off by default)

Output: list of SymbolEntry with stable AST fingerprints.
"""
import ast
import os
from pathlib import Path
from typing import Iterator

from cas_extractor.models.evidence import Anchor, SymbolEntry
from cas_extractor.utils.fingerprint import fingerprint_ast


def extract_symbols(repo_root: str, include_variables: bool = False) -> Iterator[SymbolEntry]:
    """
    Walk repo and yield SymbolEntry for every Python symbol found.

    Args:
        repo_root: Absolute or relative path to repository root
        include_variables: Whether to include module-level variable assignments

    Yields:
        SymbolEntry instances
    """
    root = Path(repo_root).resolve()

    for py_file in sorted(root.rglob("*.py")):
        # Skip hidden dirs, __pycache__, venvs
        rel = py_file.relative_to(root)
        parts = rel.parts
        if any(p.startswith(".") or p == "__pycache__" or p in ("venv", ".venv", "node_modules") for p in parts):
            continue

        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(rel))
        except (SyntaxError, UnicodeDecodeError):
            continue

        module_qname = _path_to_module(rel)
        yield from _extract_from_module(tree, source, str(rel), module_qname, include_variables)


def _path_to_module(rel_path: Path) -> str:
    """Convert file path to Python module qualified name."""
    parts = list(rel_path.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].removesuffix(".py")
    return ".".join(parts)


def _extract_from_module(
    tree: ast.Module,
    source: str,
    rel_file: str,
    module_qname: str,
    include_variables: bool,
) -> Iterator[SymbolEntry]:
    """Extract symbols from a parsed module AST."""
    source_lines = source.splitlines(keepends=True)

    # Module itself
    yield SymbolEntry(
        qualified_name=module_qname,
        kind="module",
        anchor=Anchor(
            file=rel_file,
            line_start=1,
            line_end=len(source_lines),
            qualified_symbol=module_qname,
            fingerprint=fingerprint_ast(source),
        ),
        docstring=ast.get_docstring(tree),
    )

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield _function_entry(node, source_lines, rel_file, module_qname, tree)
        elif isinstance(node, ast.ClassDef):
            yield _class_entry(node, source_lines, rel_file, module_qname, tree)


def _get_parent_qname(node: ast.AST, tree: ast.Module, module_qname: str) -> str:
    """Walk tree to find parent class/function for qualified naming."""
    # We annotate parents during walk
    for parent_node in ast.walk(tree):
        for child in ast.iter_child_nodes(parent_node):
            if child is node:
                if isinstance(parent_node, ast.ClassDef):
                    return f"{module_qname}.{parent_node.name}"
                elif isinstance(parent_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return f"{module_qname}.{parent_node.name}"
                else:
                    return module_qname
    return module_qname


def _extract_source(source_lines: list[str], node: ast.AST) -> str:
    """Extract source text for a node."""
    start = node.lineno - 1
    end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start + 1
    return "".join(source_lines[start:end])


def _function_entry(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    source_lines: list[str],
    rel_file: str,
    module_qname: str,
    tree: ast.Module,
) -> SymbolEntry:
    """Create SymbolEntry for a function/method."""
    parent_qname = _get_parent_qname(node, tree, module_qname)
    qname = f"{parent_qname}.{node.name}"
    src = _extract_source(source_lines, node)

    # Determine if method (parent is class)
    is_method = False
    for parent_node in ast.walk(tree):
        for child in ast.iter_child_nodes(parent_node):
            if child is node and isinstance(parent_node, ast.ClassDef):
                is_method = True
                break

    # Extract parameters
    params = []
    for arg in node.args.args:
        param = {"name": arg.arg}
        if arg.annotation:
            try:
                param["annotation"] = ast.unparse(arg.annotation)
            except Exception:
                pass
        params.append(param)

    # Return annotation
    ret_ann = None
    if node.returns:
        try:
            ret_ann = ast.unparse(node.returns)
        except Exception:
            pass

    # Decorators
    decorators = []
    for dec in node.decorator_list:
        try:
            decorators.append(ast.unparse(dec))
        except Exception:
            decorators.append("?")

    return SymbolEntry(
        qualified_name=qname,
        kind="method" if is_method else "function",
        anchor=Anchor(
            file=rel_file,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            qualified_symbol=qname,
            fingerprint=fingerprint_ast(src),
        ),
        decorators=decorators,
        parameters=params,
        return_annotation=ret_ann,
        docstring=ast.get_docstring(node),
    )


def _class_entry(
    node: ast.ClassDef,
    source_lines: list[str],
    rel_file: str,
    module_qname: str,
    tree: ast.Module,
) -> SymbolEntry:
    """Create SymbolEntry for a class."""
    parent_qname = _get_parent_qname(node, tree, module_qname)
    qname = f"{parent_qname}.{node.name}"
    src = _extract_source(source_lines, node)

    decorators = []
    for dec in node.decorator_list:
        try:
            decorators.append(ast.unparse(dec))
        except Exception:
            decorators.append("?")

    return SymbolEntry(
        qualified_name=qname,
        kind="class",
        anchor=Anchor(
            file=rel_file,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            qualified_symbol=qname,
            fingerprint=fingerprint_ast(src),
        ),
        decorators=decorators,
        docstring=ast.get_docstring(node),
    )
