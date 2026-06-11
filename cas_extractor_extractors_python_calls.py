"""
Python Call Graph Extractor — produces py.callgraph evidence (E1).

v0.2 CHANGES:
  - self.method() → CurrentClass.method resolution
  - cls.method() → CurrentClass.method resolution (for @classmethod)
  - super().method() → first declared BaseClass.method (if locally resolvable)
  - Proper class-aware enclosing function detection via _parent annotation
  - Still CONSERVATIVE: unresolvable → unresolved + issue, never false edges

Resolution types:
  - static: same-module direct call
  - qualified: via known import
  - self_dispatch: self.method() resolved to class method
  - cls_dispatch: cls.method() resolved to class method
  - super_dispatch: super().method() resolved to base class method
  - unresolved: could not determine target
"""
import ast
from pathlib import Path
from typing import Iterator

from cas_extractor.models.evidence import Anchor, CallEntry
from cas_extractor.utils.fingerprint import fingerprint_ast


def extract_calls(repo_root: str) -> Iterator[CallEntry]:
    """
    Walk repo and yield CallEntry for every static call found.
    v0.2: class-aware resolution for self/cls/super.
    """
    root = Path(repo_root).resolve()

    # First pass: collect all known symbols, imports, and class info per module
    module_symbols: dict[str, set[str]] = {}       # module -> {symbol_names}
    module_imports: dict[str, dict[str, str]] = {}  # module -> {local_name -> qualified_target}
    module_classes: dict[str, dict[str, ClassInfo]] = {}  # module -> {class_name -> ClassInfo}

    py_files = []
    for py_file in sorted(root.rglob("*.py")):
        rel = py_file.relative_to(root)
        parts = rel.parts
        if any(p.startswith(".") or p == "__pycache__" or p in ("venv", ".venv", "node_modules") for p in parts):
            continue
        py_files.append((py_file, rel))

    for py_file, rel in py_files:
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(rel))
        except (SyntaxError, UnicodeDecodeError):
            continue

        module_qname = _path_to_module(rel)
        symbols = set()
        imports = {}
        classes = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.add(node.name)
            elif isinstance(node, ast.ClassDef):
                symbols.add(node.name)
                ci = ClassInfo(
                    qname=f"{module_qname}.{node.name}",
                    methods=set(),
                    base_names=[],
                )
                # Collect methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        ci.methods.add(item.name)
                # Collect base class names (as written in source)
                for base in node.bases:
                    try:
                        ci.base_names.append(ast.unparse(base))
                    except Exception:
                        pass
                classes[node.name] = ci
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[-1]
                    imports[local] = alias.name
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                for alias in node.names:
                    local = alias.asname or alias.name
                    imports[local] = f"{base}.{alias.name}" if base else alias.name

        module_symbols[module_qname] = symbols
        module_imports[module_qname] = imports
        module_classes[module_qname] = classes

    # Build cross-module class index: qualified_name -> ClassInfo
    all_classes: dict[str, ClassInfo] = {}
    for mod, classes in module_classes.items():
        for cname, ci in classes.items():
            all_classes[ci.qname] = ci

    # Second pass: extract calls with class-aware resolution
    for py_file, rel in py_files:
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(rel))
        except (SyntaxError, UnicodeDecodeError):
            continue

        _annotate_parents(tree)
        source_lines = source.splitlines(keepends=True)
        module_qname = _path_to_module(rel)
        local_symbols = module_symbols.get(module_qname, set())
        local_imports = module_imports.get(module_qname, {})
        local_classes = module_classes.get(module_qname, {})

        yield from _extract_calls_from_tree(
            tree, source_lines, str(rel), module_qname,
            local_symbols, local_imports, local_classes, all_classes,
        )


class ClassInfo:
    """Lightweight class metadata for call resolution."""
    __slots__ = ("qname", "methods", "base_names")

    def __init__(self, qname: str, methods: set[str], base_names: list[str]):
        self.qname = qname
        self.methods = methods
        self.base_names = base_names


def _annotate_parents(tree: ast.AST) -> None:
    """Annotate every node with a _parent reference."""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child._parent = node  # type: ignore[attr-defined]


def _extract_calls_from_tree(
    tree: ast.Module,
    source_lines: list[str],
    rel_file: str,
    module_qname: str,
    local_symbols: set[str],
    local_imports: dict[str, str],
    local_classes: dict[str, "ClassInfo"],
    all_classes: dict[str, "ClassInfo"],
) -> Iterator[CallEntry]:
    """Extract call entries from a module's AST. v0.2: class-aware."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        # Find enclosing function AND enclosing class
        enclosing_func, enclosing_class = _find_enclosing_context(node, module_qname)

        callee, resolution = _resolve_call(
            node.func, module_qname, local_symbols, local_imports,
            local_classes, all_classes, enclosing_class,
        )

        if callee is None:
            continue

        src_text = _extract_source(source_lines, node)
        anchor = Anchor(
            file=rel_file,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            qualified_symbol=f"{enclosing_func}::call:{callee}",
            fingerprint=fingerprint_ast(src_text) if src_text.strip() else "",
        )

        yield CallEntry(
            caller=enclosing_func,
            callee=callee,
            anchor=anchor,
            resolution=resolution,
        )


def _resolve_call(
    func_node: ast.expr,
    module_qname: str,
    local_symbols: set[str],
    local_imports: dict[str, str],
    local_classes: dict[str, "ClassInfo"],
    all_classes: dict[str, "ClassInfo"],
    enclosing_class: "ClassInfo | None",
) -> tuple[str | None, str]:
    """
    Resolve a call target to a qualified name.
    v0.2: handles self.method(), cls.method(), super().method()

    Returns:
        (qualified_name, resolution_type) or (None, "skip")
    """
    # Case 1: Simple name call — foo()
    if isinstance(func_node, ast.Name):
        name = func_node.id

        # Known local symbol
        if name in local_symbols:
            return f"{module_qname}.{name}", "static"

        # Known import
        if name in local_imports:
            return local_imports[name], "qualified"

        # Builtins — skip
        if name in _BUILTINS:
            return None, "skip"

        # cls() bare call inside @classmethod → constructor of enclosing class
        if name == "cls" and enclosing_class is not None:
            return enclosing_class.qname, "cls_dispatch"

        # Unresolved
        return f"?.{name}", "unresolved"

    # Case 2: Attribute call — something.method()
    if isinstance(func_node, ast.Attribute):
        method_name = func_node.attr

        # Case 2a: self.method()
        if isinstance(func_node.value, ast.Name) and func_node.value.id == "self":
            if enclosing_class is not None:
                if method_name in enclosing_class.methods:
                    return f"{enclosing_class.qname}.{method_name}", "self_dispatch"
                else:
                    # Method not found on current class — could be inherited
                    # Try base classes (single level only)
                    resolved = _resolve_in_bases(
                        method_name, enclosing_class, local_classes, all_classes, local_imports
                    )
                    if resolved:
                        return resolved, "self_dispatch"
                    # Truly unresolved self.method()
                    return f"?.self.{method_name}", "unresolved"
            return f"?.self.{method_name}", "unresolved"

        # Case 2b: cls.method() (inside @classmethod)
        if isinstance(func_node.value, ast.Name) and func_node.value.id == "cls":
            if enclosing_class is not None:
                if method_name in enclosing_class.methods:
                    return f"{enclosing_class.qname}.{method_name}", "cls_dispatch"
            return f"?.cls.{method_name}", "unresolved"

        # Case 2c: super().method()
        if (isinstance(func_node.value, ast.Call)
                and isinstance(func_node.value.func, ast.Name)
                and func_node.value.func.id == "super"):
            if enclosing_class is not None:
                resolved = _resolve_super_method(
                    method_name, enclosing_class, local_classes, all_classes, local_imports
                )
                if resolved:
                    return resolved, "super_dispatch"
            return f"?.super().{method_name}", "unresolved"

        # Case 2d: Regular attribute call — obj.method()
        if isinstance(func_node.value, ast.Name):
            obj_name = func_node.value.id

            # Known import
            if obj_name in local_imports:
                return f"{local_imports[obj_name]}.{method_name}", "qualified"

            # Local class used as namespace (e.g., ClassName.static_method())
            if obj_name in local_classes:
                ci = local_classes[obj_name]
                if method_name in ci.methods:
                    return f"{ci.qname}.{method_name}", "static"

            # Unresolved
            return f"?.{obj_name}.{method_name}", "unresolved"

    # Everything else: too complex
    return None, "skip"


def _resolve_in_bases(
    method_name: str,
    class_info: "ClassInfo",
    local_classes: dict[str, "ClassInfo"],
    all_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
) -> str | None:
    """
    Try to find method_name in the base classes of class_info.
    Only single-level lookup (no full MRO).
    """
    for base_name in class_info.base_names:
        base_ci = _find_class_by_name(base_name, local_classes, all_classes, local_imports)
        if base_ci and method_name in base_ci.methods:
            return f"{base_ci.qname}.{method_name}"
    return None


def _resolve_super_method(
    method_name: str,
    class_info: "ClassInfo",
    local_classes: dict[str, "ClassInfo"],
    all_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
) -> str | None:
    """
    Resolve super().method() to the first base class that has the method.
    Only checks declared bases, no full MRO.
    """
    for base_name in class_info.base_names:
        base_ci = _find_class_by_name(base_name, local_classes, all_classes, local_imports)
        if base_ci and method_name in base_ci.methods:
            return f"{base_ci.qname}.{method_name}"
    return None


def _find_class_by_name(
    name: str,
    local_classes: dict[str, "ClassInfo"],
    all_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
) -> "ClassInfo | None":
    """
    Find a ClassInfo by its short name or qualified name.
    Checks: local classes, then imported names resolved to all_classes.
    """
    # Direct local match
    if name in local_classes:
        return local_classes[name]

    # Imported name → resolve to qualified → look up in all_classes
    if name in local_imports:
        qualified = local_imports[name]
        if qualified in all_classes:
            return all_classes[qualified]

    # Qualified name directly
    if name in all_classes:
        return all_classes[name]

    return None


def _find_enclosing_context(
    node: ast.AST, module_qname: str
) -> tuple[str, "ClassInfo | None"]:
    """
    Walk _parent chain to find enclosing function qname and enclosing class.
    Returns (enclosing_function_qname, enclosing_ClassInfo_or_None).
    """
    # Build the qualified name by walking up
    func_parts = []
    enclosing_class_node = None
    current = node

    while hasattr(current, '_parent'):
        parent = current._parent  # type: ignore[attr-defined]
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_parts.append(parent.name)
        elif isinstance(parent, ast.ClassDef):
            func_parts.append(parent.name)
            if enclosing_class_node is None:
                enclosing_class_node = parent
        current = parent

    func_parts.reverse()
    if func_parts:
        func_qname = f"{module_qname}.{'.'.join(func_parts)}"
    else:
        func_qname = module_qname

    # Build ClassInfo for enclosing class if found
    enclosing_class = None
    if enclosing_class_node is not None:
        class_qname = f"{module_qname}"
        # Walk up from class node to build its qname
        class_parts = [enclosing_class_node.name]
        c = enclosing_class_node
        while hasattr(c, '_parent'):
            p = c._parent  # type: ignore[attr-defined]
            if isinstance(p, ast.ClassDef):
                class_parts.append(p.name)
            c = p
        class_parts.reverse()
        class_qname = f"{module_qname}.{'.'.join(class_parts)}"

        methods = set()
        for item in enclosing_class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.add(item.name)

        base_names = []
        for base in enclosing_class_node.bases:
            try:
                base_names.append(ast.unparse(base))
            except Exception:
                pass

        enclosing_class = ClassInfo(
            qname=class_qname,
            methods=methods,
            base_names=base_names,
        )

    return func_qname, enclosing_class


def _path_to_module(rel_path: Path) -> str:
    parts = list(rel_path.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].removesuffix(".py")
    return ".".join(parts)


def _extract_source(source_lines: list[str], node: ast.AST) -> str:
    start = node.lineno - 1
    end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start + 1
    return "".join(source_lines[start:end])


# Common builtins we skip in callgraph
_BUILTINS = frozenset({
    "print", "len", "range", "enumerate", "zip", "map", "filter",
    "sorted", "reversed", "list", "dict", "set", "tuple", "str",
    "int", "float", "bool", "type", "isinstance", "issubclass",
    "hasattr", "getattr", "setattr", "delattr", "super", "property",
    "staticmethod", "classmethod", "abs", "min", "max", "sum",
    "any", "all", "open", "input", "repr", "hash", "id", "dir",
    "vars", "globals", "locals", "callable", "iter", "next",
    "format", "chr", "ord", "hex", "oct", "bin",
    "ValueError", "TypeError", "KeyError", "IndexError",
    "AttributeError", "RuntimeError", "Exception", "StopIteration",
    "NotImplementedError", "FileNotFoundError", "OSError",
    "ImportError", "ModuleNotFoundError",
    "frozenset", "bytes", "bytearray", "memoryview",
    "divmod", "round", "pow", "complex",
    "KeyboardInterrupt", "SystemError", "SystemExit",
    "OverflowError", "ZeroDivisionError", "AssertionError",
    "UnicodeError", "UnicodeDecodeError", "UnicodeEncodeError",
    "PermissionError", "TimeoutError", "ConnectionError",
    "BrokenPipeError", "EOFError", "GeneratorExit",
    "object", "breakpoint", "compile", "eval", "exec",
    "staticmethod", "classmethod",
})
