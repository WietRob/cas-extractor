"""
Python Call Graph Extractor — produces py.callgraph evidence (E1).

v0.2 CHANGES:
  - self.method() → CurrentClass.method resolution
  - cls.method() → CurrentClass.method resolution (for @classmethod)
  - super().method() → first declared BaseClass.method (if locally resolvable)
  - Proper class-aware enclosing function detection via _parent annotation
  - Still CONSERVATIVE: unresolvable → unresolved + issue, never false edges

v0.3 CHANGES (H3):
  - ClassName().method() → ClassName.method resolution (ctor_dispatch)

v0.3b CHANGES (H1):
  - x = ClassName(); x.method() → ClassName.method resolution (local_var_dispatch)
  - Intra-function scope only, last assignment wins

v0.3c CHANGES (H2):
  - self.attr.method() → ClassName.method resolution (self_attr_dispatch)
  - Only self.attr = ClassName() in __init__ tracked
  - Intra-class scope only, last assignment wins

Resolution types:
  - static: same-module direct call
  - qualified: via known import
  - self_dispatch: self.method() resolved to class method
  - cls_dispatch: cls.method() resolved to class method
  - super_dispatch: super().method() resolved to base class method
  - ctor_dispatch: ClassName().method() resolved to instance method
  - local_var_dispatch: x.method() where x = ClassName() in same scope
  - self_attr_dispatch: self.attr.method() where self.attr = ClassName() in __init__
  - unresolved: could not determine target
"""

import ast
from pathlib import Path
from typing import Iterator

from cas_extractor.models.evidence import Anchor, CallEntry
from cas_extractor.resolvers import create_resolution_engine, CallContext
from cas_extractor.resolvers.base import ClassInfo as ResolverClassInfo
from cas_extractor.utils.fingerprint import fingerprint_ast


def extract_calls(
    repo_root: str,
    emit_unresolved_self_attr: bool = True,
    enable_h25_self_attr_noninit: bool = False,
    enable_h26_self_attr_intermethod: bool = False,
    h26_max_helper_depth: int = 2,
    enable_h27_self_attr_transitive: bool = False,
    h27_max_chain_depth: int = 2,
    enable_h28_factory_return: bool = False,
    h28_max_factory_depth: int = 1,
    enable_h29_resolution_metadata: bool = False,
    enable_v050_resolution_engine: bool = False,
    v050_emit_resolution_trace: bool = False,
) -> Iterator[CallEntry]:
    """
    Walk repo and yield CallEntry for every static call found.
    v0.2: class-aware resolution for self/cls/super.
    v0.4 (H2.1): emit_unresolved_self_attr controls unresolved H2 dispatch.
    v0.4.1 (H2.5): enable_h25_self_attr_noninit enables intra-method non-__init__ resolution.
    v0.4.2 (H2.6): enable_h26_self_attr_intermethod enables inter-method propagation.
    v0.4.3 (H2.7): enable_h27_self_attr_transitive enables multi-hop transitive propagation.
    v0.4.4 (H2.8): enable_h28_factory_return enables factory return type inference.
    v0.4.5 (H2.9): enable_h29_resolution_metadata adds resolution source info.
    v0.5.0: enable_v050_resolution_engine uses ResolutionEngine instead of legacy resolver.
    """
    root = Path(repo_root).resolve()

    # First pass: collect all known symbols, imports, and class info per module
    module_symbols: dict[str, set[str]] = {}  # module -> {symbol_names}
    module_imports: dict[
        str, dict[str, str]
    ] = {}  # module -> {local_name -> qualified_target}
    module_classes: dict[
        str, dict[str, ClassInfo]
    ] = {}  # module -> {class_name -> ClassInfo}
    module_factory_types: dict[
        str, dict[str, str]
    ] = {}  # module -> {factory_name -> class_qname}

    py_files = []
    for py_file in sorted(root.rglob("*.py")):
        rel = py_file.relative_to(root)
        parts = rel.parts
        if any(
            p.startswith(".")
            or p == "__pycache__"
            or p in ("venv", ".venv", "node_modules")
            for p in parts
        ):
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

    if enable_h28_factory_return:
        for py_file, rel in py_files:
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(rel))
            except (SyntaxError, UnicodeDecodeError):
                continue

            module_qname = _path_to_module(rel)
            local_imports = module_imports.get(module_qname, {})
            local_classes = module_classes.get(module_qname, {})
            factory_types = _build_factory_return_types(
                tree, local_classes, local_imports, all_classes
            )
            if factory_types:
                module_factory_types[module_qname] = factory_types

    # H2: Post-process to populate self_attr_types for each class
    # Need to re-parse to get class nodes for __init__ analysis
    for py_file, rel in py_files:
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(rel))
        except (SyntaxError, UnicodeDecodeError):
            continue

        module_qname = _path_to_module(rel)
        local_imports = module_imports.get(module_qname, {})
        local_classes = module_classes.get(module_qname, {})
        local_factory_types = module_factory_types.get(module_qname, {})

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in local_classes:
                ci = local_classes[node.name]
                ci.self_attr_types = _build_init_self_attr_types(
                    node, local_classes, local_imports, all_classes, local_factory_types
                )
                if enable_h26_self_attr_intermethod:
                    ci.method_self_attr_summaries = _build_class_method_summaries(
                        node,
                        local_classes,
                        local_imports,
                        all_classes,
                        local_factory_types,
                    )

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
        local_factory_types = module_factory_types.get(module_qname, {})

        yield from _extract_calls_from_tree(
            tree,
            source_lines,
            str(rel),
            module_qname,
            local_symbols,
            local_imports,
            local_classes,
            all_classes,
            emit_unresolved_self_attr,
            enable_h25_self_attr_noninit,
            enable_h26_self_attr_intermethod,
            h26_max_helper_depth,
            enable_h27_self_attr_transitive,
            h27_max_chain_depth,
            enable_h28_factory_return,
            h28_max_factory_depth,
            local_factory_types,
            enable_h29_resolution_metadata,
            enable_v050_resolution_engine,
            v050_emit_resolution_trace,
        )


class ClassInfo:
    """Lightweight class metadata for call resolution."""

    __slots__ = (
        "qname",
        "methods",
        "base_names",
        "self_attr_types",
        "method_self_attr_summaries",
    )

    def __init__(
        self,
        qname: str,
        methods: set[str],
        base_names: list[str],
        self_attr_types: dict[str, str] | None = None,
        method_self_attr_summaries: dict[str, dict[str, str]] | None = None,
    ):
        self.qname = qname
        self.methods = methods
        self.base_names = base_names
        # H2: {attr_name: class_qname} for self.attr = ClassName() in __init__
        self.self_attr_types = self_attr_types or {}
        # H2.6: {method_name: {attr_name: class_qname}} for each method
        self.method_self_attr_summaries = method_self_attr_summaries or {}


def _annotate_parents(tree: ast.AST) -> None:
    """Annotate every node with a _parent reference."""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child._parent = node  # type: ignore[attr-defined]


def _build_local_var_types(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    local_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
    all_classes: dict[str, "ClassInfo"],
    factory_return_types: dict[str, str] | None = None,
) -> dict[str, str]:
    var_types: dict[str, str] = {}

    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    class_qname = _infer_class_from_expr(
                        node.value,
                        local_classes,
                        local_imports,
                        all_classes,
                        factory_return_types,
                    )
                    if class_qname:
                        var_types[var_name] = class_qname
        elif isinstance(node, ast.AnnAssign) and node.value:
            if isinstance(node.target, ast.Name):
                var_name = node.target.id
                class_qname = _infer_class_from_expr(
                    node.value,
                    local_classes,
                    local_imports,
                    all_classes,
                    factory_return_types,
                )
                if class_qname:
                    var_types[var_name] = class_qname

    return var_types


def _infer_class_from_expr(
    expr: ast.expr,
    local_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
    all_classes: dict[str, "ClassInfo"],
    factory_return_types: dict[str, str] | None = None,
) -> str | None:
    if isinstance(expr, ast.Call):
        if isinstance(expr.func, ast.Name):
            class_name = expr.func.id
            if class_name in local_classes:
                return local_classes[class_name].qname
            if class_name in local_imports:
                qualified = local_imports[class_name]
                if qualified in all_classes:
                    return qualified
            if factory_return_types and class_name in factory_return_types:
                return factory_return_types[class_name]
    return None


def _find_enclosing_func_node(
    node: ast.AST,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Find the enclosing function node by walking _parent chain."""
    current = node
    while hasattr(current, "_parent"):
        parent = current._parent  # type: ignore[attr-defined]
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent
        current = parent
    return None


def _build_init_self_attr_types(
    class_node: ast.ClassDef,
    local_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
    all_classes: dict[str, "ClassInfo"],
    factory_return_types: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    H2: Build mapping of self.attr names to their inferred class qnames.
    Only tracks: self.attr = ClassName(...) in __init__ method.
    Last assignment wins.
    """
    attr_types: dict[str, str] = {}
    init_node: ast.FunctionDef | None = None
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
            init_node = item
            break

    if init_node is None:
        return attr_types

    for node in ast.walk(init_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attr_name = target.attr
                    class_qname = _infer_class_from_expr(
                        node.value,
                        local_classes,
                        local_imports,
                        all_classes,
                        factory_return_types,
                    )
                    if class_qname:
                        attr_types[attr_name] = class_qname
        elif isinstance(node, ast.AnnAssign) and node.value:
            if (
                isinstance(node.target, ast.Attribute)
                and isinstance(node.target.value, ast.Name)
                and node.target.value.id == "self"
            ):
                attr_name = node.target.attr
                class_qname = _infer_class_from_expr(
                    node.value,
                    local_classes,
                    local_imports,
                    all_classes,
                    factory_return_types,
                )
                if class_qname:
                    attr_types[attr_name] = class_qname

    return attr_types


def _build_method_local_self_attr_types(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    local_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
    all_classes: dict[str, "ClassInfo"],
    factory_return_types: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    H2.5: Build mapping of self.attr names to their inferred class qnames.
    Only tracks: self.attr = ClassName(...) in current method (not __init__).
    Last assignment wins within method scope.
    Used for intra-method write-before-use resolution.
    """
    attr_types: dict[str, str] = {}

    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attr_name = target.attr
                    class_qname = _infer_class_from_expr(
                        node.value,
                        local_classes,
                        local_imports,
                        all_classes,
                        factory_return_types,
                    )
                    if class_qname:
                        attr_types[attr_name] = class_qname
        elif isinstance(node, ast.AnnAssign) and node.value:
            if (
                isinstance(node.target, ast.Attribute)
                and isinstance(node.target.value, ast.Name)
                and node.target.value.id == "self"
            ):
                attr_name = node.target.attr
                class_qname = _infer_class_from_expr(
                    node.value,
                    local_classes,
                    local_imports,
                    all_classes,
                    factory_return_types,
                )
                if class_qname:
                    attr_types[attr_name] = class_qname

    return attr_types


def _build_class_method_summaries(
    class_node: ast.ClassDef,
    local_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
    all_classes: dict[str, "ClassInfo"],
    factory_return_types: dict[str, str] | None = None,
) -> dict[str, dict[str, str]]:
    """
    H2.6: Build self.attr summaries for each method in a class.
    Returns: {method_name: {attr_name: class_qname}}
    """
    summaries: dict[str, dict[str, str]] = {}
    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            summaries[item.name] = _build_method_local_self_attr_types(
                item, local_classes, local_imports, all_classes, factory_return_types
            )
    return summaries


def _build_factory_return_types(
    tree: ast.Module,
    local_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
    all_classes: dict[str, "ClassInfo"],
) -> dict[str, str]:
    """
    H2.8: Build mapping of module-level function names to their return class types.
    Only includes functions with a single, direct `return ClassName()` pattern.
    Returns: {function_name: class_qname}
    """
    factory_types: dict[str, str] = {}

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        return_type = _get_direct_return_class(
            node, local_classes, local_imports, all_classes
        )
        if return_type:
            factory_types[node.name] = return_type

    return factory_types


def _get_direct_return_class(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    local_classes: dict[str, "ClassInfo"],
    local_imports: dict[str, str],
    all_classes: dict[str, "ClassInfo"],
) -> str | None:
    """
    H2.8: Check if function has a single direct return ClassName() pattern.
    Returns class_qname if valid factory, None otherwise.
    """
    return_stmts = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Return) and node.value is not None:
            return_stmts.append(node.value)

    if len(return_stmts) != 1:
        return None

    ret_expr = return_stmts[0]

    if not isinstance(ret_expr, ast.Call):
        return None

    if not isinstance(ret_expr.func, ast.Name):
        return None

    class_name = ret_expr.func.id

    if class_name in local_classes:
        return local_classes[class_name].qname
    if class_name in local_imports:
        qualified = local_imports[class_name]
        if qualified in all_classes:
            return qualified

    return None


def _get_self_calls_in_method(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    class_methods: set[str],
) -> list[str]:
    """
    H2.6: Find all self.method() calls within a method body.
    Returns list of called method names that exist in the class.
    """
    called_methods: list[str] = []
    for node in ast.walk(func_node):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
        ):
            method_name = node.func.attr
            if method_name in class_methods:
                called_methods.append(method_name)
    return called_methods


def _propagate_self_attr_summaries(
    class_node: ast.ClassDef,
    initial_summaries: dict[str, dict[str, str]],
    class_methods: set[str],
    max_depth: int = 2,
) -> dict[str, dict[str, str | None]]:
    """
    H2.6: Propagate self.attr types through self.helper() calls.
    Returns: {caller_method: {attr_name: class_qname | None}}
    None indicates conflict (same attr, different types from different helpers).
    """
    method_nodes: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_nodes[item.name] = item

    propagated: dict[str, dict[str, str | None]] = {
        m: dict(attrs) for m, attrs in initial_summaries.items()
    }
    visiting: set[str] = set()

    def propagate(method_name: str, depth: int) -> dict[str, str | None]:
        if depth > max_depth or method_name in visiting:
            return {}
        if method_name not in method_nodes:
            return {}

        visiting.add(method_name)
        result: dict[str, str | None] = dict(propagated.get(method_name, {}))

        called_methods = _get_self_calls_in_method(
            method_nodes[method_name], class_methods
        )

        for callee_name in called_methods:
            if callee_name == method_name:
                continue
            callee_attrs = propagate(callee_name, depth + 1)
            for attr, class_qname in callee_attrs.items():
                if class_qname is None:
                    continue
                if attr not in result:
                    result[attr] = class_qname
                elif result.get(attr) != class_qname:
                    result[attr] = None

        visiting.discard(method_name)
        return result

    for method_name in list(method_nodes.keys()):
        propagated[method_name] = propagate(method_name, 0)

    return propagated


def _extract_calls_from_tree(
    tree: ast.Module,
    source_lines: list[str],
    rel_file: str,
    module_qname: str,
    local_symbols: set[str],
    local_imports: dict[str, str],
    local_classes: dict[str, "ClassInfo"],
    all_classes: dict[str, "ClassInfo"],
    emit_unresolved_self_attr: bool = True,
    enable_h25_self_attr_noninit: bool = False,
    enable_h26_self_attr_intermethod: bool = False,
    h26_max_helper_depth: int = 2,
    enable_h27_self_attr_transitive: bool = False,
    h27_max_chain_depth: int = 2,
    enable_h28_factory_return: bool = False,
    h28_max_factory_depth: int = 1,
    factory_return_types: dict[str, str] | None = None,
    enable_h29_resolution_metadata: bool = False,
    enable_v050_resolution_engine: bool = False,
    v050_emit_resolution_trace: bool = False,
) -> Iterator[CallEntry]:
    """Extract call entries from a module's AST.
    v0.4 (H2.1): emit_unresolved_self_attr controls H2 unresolved dispatch.
    v0.4.1 (H2.5): enable_h25_self_attr_noninit enables intra-method resolution.
    v0.4.2 (H2.6): enable_h26_self_attr_intermethod enables inter-method propagation.
    v0.4.3 (H2.7): enable_h27_self_attr_transitive enables multi-hop transitive propagation.
    v0.4.4 (H2.8): enable_h28_factory_return enables factory return type inference.
    v0.4.5 (H2.9): enable_h29_resolution_metadata adds resolution source info.
    v0.5.0: enable_v050_resolution_engine uses ResolutionEngine."""

    engine = None
    if enable_v050_resolution_engine:
        engine = create_resolution_engine(
            enable_h25=enable_h25_self_attr_noninit,
            enable_h26_h27=(
                enable_h26_self_attr_intermethod or enable_h27_self_attr_transitive
            ),
            enable_h28_factory_return=enable_h28_factory_return,
            factory_return_types=factory_return_types,
        )

    class_propagated_summaries: dict[str, dict[str, dict[str, str | None]]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        enclosing_func, enclosing_class = _find_enclosing_context(
            node, module_qname, all_classes
        )

        enclosing_func_node = _find_enclosing_func_node(node)
        local_var_types: dict[str, str] = {}
        method_local_self_attr_types: dict[str, str] = {}
        propagated_self_attr_types: dict[str, str | None] = {}

        if enclosing_func_node is not None:
            local_var_types = _build_local_var_types(
                enclosing_func_node,
                local_classes,
                local_imports,
                all_classes,
                factory_return_types,
            )
            if enable_h25_self_attr_noninit and enclosing_func_node.name != "__init__":
                method_local_self_attr_types = _build_method_local_self_attr_types(
                    enclosing_func_node,
                    local_classes,
                    local_imports,
                    all_classes,
                    factory_return_types,
                )

        if (
            (enable_h26_self_attr_intermethod or enable_h27_self_attr_transitive)
            and enclosing_class is not None
            and enclosing_func_node is not None
        ):
            class_key = enclosing_class.qname
            if class_key not in class_propagated_summaries:
                for cls_node in ast.walk(tree):
                    if (
                        isinstance(cls_node, ast.ClassDef)
                        and f"{module_qname}.{cls_node.name}" == class_key
                    ):
                        initial = _build_class_method_summaries(
                            cls_node,
                            local_classes,
                            local_imports,
                            all_classes,
                            factory_return_types,
                        )
                        max_depth = (
                            h27_max_chain_depth
                            if enable_h27_self_attr_transitive
                            else h26_max_helper_depth
                        )
                        propagated = _propagate_self_attr_summaries(
                            cls_node,
                            initial,
                            enclosing_class.methods,
                            max_depth,
                        )
                        class_propagated_summaries[class_key] = propagated
                        break

            class_propagated = class_propagated_summaries.get(class_key, {})
            method_name = enclosing_func_node.name
            if method_name in class_propagated:
                propagated_self_attr_types = class_propagated[method_name]

        if engine is not None:
            context = CallContext(
                func_node=node.func,
                enclosing_func=enclosing_func,
                enclosing_class=enclosing_class,
                local_var_types=local_var_types,
                method_local_self_attr_types=method_local_self_attr_types,
                propagated_self_attr_types=propagated_self_attr_types,
                self_attr_types=enclosing_class.self_attr_types
                if enclosing_class
                else {},
                factory_return_types=factory_return_types or {},
                module_qname=module_qname,
                local_symbols=local_symbols,
                local_imports=local_imports,
                local_classes=local_classes,
                all_classes=all_classes,
                emit_unresolved_self_attr=emit_unresolved_self_attr,
            )
            result = engine.resolve(context)
            if result.callee is None or result.callee == "?.skip":
                continue
            if result.callee and result.callee.startswith("?."):
                continue
            callee = result.callee
            resolution = result.resolution_type
            resolution_source = (
                result.heuristic if enable_h29_resolution_metadata else None
            )
            resolution_detail = None
            if v050_emit_resolution_trace and result.trace:
                resolution_detail = {
                    "trace": [
                        {
                            "heuristic": step.heuristic,
                            "pattern": step.pattern_matched,
                            "inferred_type": step.inferred_type,
                            "reasoning": step.reasoning,
                        }
                        for step in result.trace
                    ]
                }
        else:
            callee, resolution = _resolve_call(
                node.func,
                module_qname,
                local_symbols,
                local_imports,
                local_classes,
                all_classes,
                enclosing_class,
                local_var_types,
                method_local_self_attr_types,
                propagated_self_attr_types,
                emit_unresolved_self_attr,
            )
            resolution_source = (
                _get_resolution_source(
                    resolution,
                    local_var_types,
                    method_local_self_attr_types,
                    propagated_self_attr_types,
                    enclosing_class,
                )
                if enable_h29_resolution_metadata
                else None
            )
            resolution_detail = None

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
            resolution_source=resolution_source,
            resolution_detail=resolution_detail,
        )


def _resolve_call(
    func_node: ast.expr,
    module_qname: str,
    local_symbols: set[str],
    local_imports: dict[str, str],
    local_classes: dict[str, "ClassInfo"],
    all_classes: dict[str, "ClassInfo"],
    enclosing_class: "ClassInfo | None",
    local_var_types: dict[str, str] | None = None,
    method_local_self_attr_types: dict[str, str] | None = None,
    propagated_self_attr_types: dict[str, str | None] | None = None,
    emit_unresolved_self_attr: bool = True,
) -> tuple[str | None, str]:
    """
    Resolve a call target to a qualified name.
    v0.2: handles self.method(), cls.method(), super().method()
    v0.3b (H1): handles x.method() where x = ClassName() in same scope
    v0.4 (H2.1): emit_unresolved_self_attr controls unresolved H2 dispatch skip behavior
    v0.4.1 (H2.5): method_local_self_attr_types enables intra-method non-__init__ resolution
    v0.4.2 (H2.6): propagated_self_attr_types enables inter-method propagation

    Returns:
        (qualified_name, resolution_type) or (None, "skip")
    """
    if local_var_types is None:
        local_var_types = {}
    if method_local_self_attr_types is None:
        method_local_self_attr_types = {}
    if propagated_self_attr_types is None:
        propagated_self_attr_types = {}

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
                    resolved = _resolve_in_bases(
                        method_name,
                        enclosing_class,
                        local_classes,
                        all_classes,
                        local_imports,
                    )
                    if resolved:
                        return resolved, "self_dispatch"
                    return f"?.self.{method_name}", "unresolved"
            return f"?.self.{method_name}", "unresolved"

        # Case 2b: cls.method() (inside @classmethod)
        if isinstance(func_node.value, ast.Name) and func_node.value.id == "cls":
            if enclosing_class is not None:
                if method_name in enclosing_class.methods:
                    return f"{enclosing_class.qname}.{method_name}", "cls_dispatch"
            return f"?.cls.{method_name}", "unresolved"

        # Case 2c: super().method()
        if (
            isinstance(func_node.value, ast.Call)
            and isinstance(func_node.value.func, ast.Name)
            and func_node.value.func.id == "super"
        ):
            if enclosing_class is not None:
                resolved = _resolve_super_method(
                    method_name,
                    enclosing_class,
                    local_classes,
                    all_classes,
                    local_imports,
                )
                if resolved:
                    return resolved, "super_dispatch"
            return f"?.super().{method_name}", "unresolved"

        # Case 2d: H2/H2.5/H2.6 - self.attr.method() where self.attr = ClassName()
        if (
            isinstance(func_node.value, ast.Attribute)
            and isinstance(func_node.value.value, ast.Name)
            and func_node.value.value.id == "self"
            and enclosing_class is not None
        ):
            attr_name = func_node.value.attr
            method_name = func_node.attr

            # H2.5: Check method-local first (highest priority)
            if attr_name in method_local_self_attr_types:
                class_qname = method_local_self_attr_types[attr_name]
                ci = all_classes.get(class_qname)
                if ci and method_name in ci.methods:
                    return f"{ci.qname}.{method_name}", "self_attr_dispatch"

            # H2.6: Check propagated from called helpers
            if attr_name in propagated_self_attr_types:
                class_qname = propagated_self_attr_types[attr_name]
                if class_qname is not None:
                    ci = all_classes.get(class_qname)
                    if ci and method_name in ci.methods:
                        return f"{ci.qname}.{method_name}", "self_attr_dispatch"

            # H2: Fall back to class-level (__init__)
            if attr_name in enclosing_class.self_attr_types:
                class_qname = enclosing_class.self_attr_types[attr_name]
                ci = all_classes.get(class_qname)
                if ci and method_name in ci.methods:
                    return f"{ci.qname}.{method_name}", "self_attr_dispatch"

            # H2.1: skip unresolved when flag is False
            if not emit_unresolved_self_attr:
                return None, "skip"
            return f"?.self.{attr_name}.{method_name}", "unresolved"

        # Case 2e: Regular attribute call — obj.method()
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

            # H1: Local variable with inferred class type (x = ClassName(); x.method())
            if obj_name in local_var_types:
                class_qname = local_var_types[obj_name]
                ci = all_classes.get(class_qname)
                if ci and method_name in ci.methods:
                    return f"{ci.qname}.{method_name}", "local_var_dispatch"

            # Unresolved
            return f"?.{obj_name}.{method_name}", "unresolved"

        # Case 2e: Constructor chain — ClassName().method()
        # H3: Direct class instantiation followed by method call
        if isinstance(func_node.value, ast.Call):
            # Check if the call is a simple constructor: ClassName()
            if isinstance(func_node.value.func, ast.Name):
                class_name = func_node.value.func.id

                # Local class
                if class_name in local_classes:
                    ci = local_classes[class_name]
                    if method_name in ci.methods:
                        return f"{ci.qname}.{method_name}", "ctor_dispatch"

                # Imported class
                if class_name in local_imports:
                    qualified = local_imports[class_name]
                    if qualified in all_classes:
                        ci = all_classes[qualified]
                        if method_name in ci.methods:
                            return f"{ci.qname}.{method_name}", "ctor_dispatch"

            # Complex constructor (factory, chained) — skip for now
            # This is H1/H2 territory, not H3

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
        base_ci = _find_class_by_name(
            base_name, local_classes, all_classes, local_imports
        )
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
        base_ci = _find_class_by_name(
            base_name, local_classes, all_classes, local_imports
        )
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
    node: ast.AST, module_qname: str, all_classes: dict[str, "ClassInfo"]
) -> tuple[str, "ClassInfo | None"]:
    """
    Walk _parent chain to find enclosing function qname and enclosing class.
    Returns (enclosing_function_qname, enclosing_ClassInfo_or_None).
    H2: Look up pre-built ClassInfo from all_classes to get self_attr_types.
    """
    func_parts = []
    enclosing_class_node = None
    current = node

    while hasattr(current, "_parent"):
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

    enclosing_class = None
    if enclosing_class_node is not None:
        class_parts = [enclosing_class_node.name]
        c = enclosing_class_node
        while hasattr(c, "_parent"):
            p = c._parent  # type: ignore[attr-defined]
            if isinstance(p, ast.ClassDef):
                class_parts.append(p.name)
            c = p
        class_parts.reverse()
        class_qname = f"{module_qname}.{'.'.join(class_parts)}"

        ci = all_classes.get(class_qname)
        if ci is not None:
            enclosing_class = ci
        else:
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
    end = (
        node.end_lineno
        if hasattr(node, "end_lineno") and node.end_lineno
        else start + 1
    )
    return "".join(source_lines[start:end])


def _get_resolution_source(
    resolution: str,
    local_var_types: dict[str, str],
    method_local_self_attr_types: dict[str, str],
    propagated_self_attr_types: dict[str, str | None],
    enclosing_class: "ClassInfo | None",
) -> str:
    """
    H2.9: Determine which heuristic resolved the call based on resolution type.
    Returns heuristic name like 'H1', 'H2', 'H2.5', 'H2.6', 'H2.7', 'H2.8', 'H3'.
    """
    if resolution == "local_var_dispatch":
        return "H1"
    if resolution == "ctor_dispatch":
        return "H3"
    if resolution == "self_dispatch":
        return "self.method"
    if resolution == "cls_dispatch":
        return "cls.method"
    if resolution == "super_dispatch":
        return "super.method"
    if resolution == "static" or resolution == "qualified":
        return "module-level"
    if resolution == "self_attr_dispatch":
        if method_local_self_attr_types:
            return "H2.5"
        if propagated_self_attr_types:
            return "H2.6/2.7"
        if enclosing_class and enclosing_class.self_attr_types:
            return "H2"
        return "H2"
    if resolution == "unresolved":
        return "unresolved"
    return "unknown"


# Common builtins we skip in callgraph
_BUILTINS = frozenset(
    {
        "print",
        "len",
        "range",
        "enumerate",
        "zip",
        "map",
        "filter",
        "sorted",
        "reversed",
        "list",
        "dict",
        "set",
        "tuple",
        "str",
        "int",
        "float",
        "bool",
        "type",
        "isinstance",
        "issubclass",
        "hasattr",
        "getattr",
        "setattr",
        "delattr",
        "super",
        "property",
        "staticmethod",
        "classmethod",
        "abs",
        "min",
        "max",
        "sum",
        "any",
        "all",
        "open",
        "input",
        "repr",
        "hash",
        "id",
        "dir",
        "vars",
        "globals",
        "locals",
        "callable",
        "iter",
        "next",
        "format",
        "chr",
        "ord",
        "hex",
        "oct",
        "bin",
        "ValueError",
        "TypeError",
        "KeyError",
        "IndexError",
        "AttributeError",
        "RuntimeError",
        "Exception",
        "StopIteration",
        "NotImplementedError",
        "FileNotFoundError",
        "OSError",
        "ImportError",
        "ModuleNotFoundError",
        "frozenset",
        "bytes",
        "bytearray",
        "memoryview",
        "divmod",
        "round",
        "pow",
        "complex",
        "KeyboardInterrupt",
        "SystemError",
        "SystemExit",
        "OverflowError",
        "ZeroDivisionError",
        "AssertionError",
        "UnicodeError",
        "UnicodeDecodeError",
        "UnicodeEncodeError",
        "PermissionError",
        "TimeoutError",
        "ConnectionError",
        "BrokenPipeError",
        "EOFError",
        "GeneratorExit",
        "object",
        "breakpoint",
        "compile",
        "eval",
        "exec",
        "staticmethod",
        "classmethod",
    }
)
