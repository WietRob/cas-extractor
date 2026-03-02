"""
Python Import Graph Extractor — produces py.importgraph evidence (E0).

Extracts all import and from...import statements from Python files.
Resolves relative imports to absolute module paths where possible.
"""
import ast
from pathlib import Path
from typing import Iterator

from cas_extractor.models.evidence import Anchor, ImportEntry
from cas_extractor.utils.fingerprint import fingerprint_ast


def extract_imports(repo_root: str) -> Iterator[ImportEntry]:
    """
    Walk repo and yield ImportEntry for every import found.

    Args:
        repo_root: Path to repository root

    Yields:
        ImportEntry instances
    """
    root = Path(repo_root).resolve()

    for py_file in sorted(root.rglob("*.py")):
        rel = py_file.relative_to(root)
        parts = rel.parts
        if any(p.startswith(".") or p == "__pycache__" or p in ("venv", ".venv", "node_modules") for p in parts):
            continue

        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(rel))
        except (SyntaxError, UnicodeDecodeError):
            continue

        source_lines = source.splitlines(keepends=True)
        module_qname = _path_to_module(rel)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    src_text = _extract_source(source_lines, node)
                    yield ImportEntry(
                        source_module=module_qname,
                        target=alias.name,
                        alias=alias.asname,
                        is_from_import=False,
                        anchor=Anchor(
                            file=str(rel),
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            qualified_symbol=f"{module_qname}::import:{alias.name}",
                            fingerprint=fingerprint_ast(src_text),
                        ),
                    )

            elif isinstance(node, ast.ImportFrom):
                base_module = _resolve_relative_import(
                    node.module, node.level, module_qname
                )
                for alias in node.names:
                    target = f"{base_module}.{alias.name}" if base_module else alias.name
                    src_text = _extract_source(source_lines, node)
                    yield ImportEntry(
                        source_module=module_qname,
                        target=target,
                        alias=alias.asname,
                        is_from_import=True,
                        anchor=Anchor(
                            file=str(rel),
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            qualified_symbol=f"{module_qname}::from:{target}",
                            fingerprint=fingerprint_ast(src_text),
                        ),
                    )


def _path_to_module(rel_path: Path) -> str:
    parts = list(rel_path.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].removesuffix(".py")
    return ".".join(parts)


def _resolve_relative_import(module: str | None, level: int, current_module: str) -> str:
    """Resolve relative import to absolute module path."""
    if level == 0:
        return module or ""

    parts = current_module.split(".")
    # Go up 'level' packages
    if level <= len(parts):
        base = ".".join(parts[:-level])
    else:
        base = ""

    if module:
        return f"{base}.{module}" if base else module
    return base


def _extract_source(source_lines: list[str], node: ast.AST) -> str:
    start = node.lineno - 1
    end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start + 1
    return "".join(source_lines[start:end])
