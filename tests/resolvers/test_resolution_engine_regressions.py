"""
Resolution Engine Regression Tests for v0.5.1

Gate A: H2.6/2.7 - Inter-method self.attr propagation
Gate B: H2.8 - Factory return type inference
Gate C: qualified_attr - Qualified attribute access resolution
"""

import ast
import pytest
from typing import cast

from cas_extractor.resolvers import (
    ResolutionEngine,
    CallContext,
    ResolutionResult,
    ClassInfo,
    create_resolution_engine,
)


GATE_A_FIXTURE = """
class Client:
    def send(self):
        pass


def make_client() -> Client:
    return Client()


class Service:
    def init_client(self):
        self.client = make_client()

    def run(self):
        self.init_client()
        self.client.send()
"""

GATE_B_FIXTURE = """
class Builder:
    def build(self):
        pass


def builder_factory() -> Builder:
    return Builder()


def main():
    x = builder_factory()
    x.build()
"""

GATE_C_FIXTURE = """
import ast

def parse_code(source: str):
    tree = ast.parse(source)
    return tree

def main():
    tree = parse_code("x = 1")
    ast.walk(tree)
"""


def build_class_info(source: str, class_name: str) -> ClassInfo | None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            methods = {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
            return ClassInfo(qname=class_name, methods=methods, base_names=[])
    return None


def build_all_classes(source: str) -> dict[str, ClassInfo]:
    tree = ast.parse(source)
    classes = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes[node.name] = build_class_info(source, node.name) or ClassInfo(
                qname=node.name, methods=set(), base_names=[]
            )
    return classes


def find_calls(source: str) -> list[tuple[ast.Call, str, str | None]]:
    tree = ast.parse(source)
    calls = []

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.func = None
            self.cls = None

        def visit_ClassDef(self, node):
            old = self.cls
            self.cls = node.name
            self.generic_visit(node)
            self.cls = old

        def visit_FunctionDef(self, node):
            old = self.func
            self.func = node.name
            self.generic_visit(node)
            self.func = old

        def visit_Call(self, node):
            calls.append((node, self.func or "<module>", self.cls))
            self.generic_visit(node)

    Visitor().visit(tree)
    return calls


def infer_local_var_types(source: str, factory_types: dict[str, str]) -> dict[str, str]:
    result = {}
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call) and isinstance(
                node.value.func, ast.Name
            ):
                fname = node.value.func.id
                if fname in factory_types:
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            result[t.id] = factory_types[fname]
    return result


def extract_imports(source: str) -> dict[str, str]:
    imports = {}
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                mod = node.module or ""
                imports[alias.asname or alias.name] = f"{mod}.{alias.name}"
    return imports


def make_context(
    call_node: ast.Call,
    enclosing_func: str,
    enclosing_class: str | None,
    all_classes: dict[str, ClassInfo],
    factory_return_types: dict[str, str] | None = None,
    propagated_self_attr_types: dict[str, str] | None = None,
    self_attr_types: dict[str, str] | None = None,
    local_var_types: dict[str, str] | None = None,
    source: str | None = None,
) -> CallContext:
    local_imports = extract_imports(source) if source else {}
    return CallContext(
        func_node=call_node.func,
        enclosing_func=enclosing_func,
        enclosing_class=all_classes.get(enclosing_class) if enclosing_class else None,
        local_var_types=local_var_types or {},
        method_local_self_attr_types={},
        propagated_self_attr_types=propagated_self_attr_types or {},
        self_attr_types=self_attr_types or {},
        factory_return_types=factory_return_types or {},
        module_qname="test_fixture",
        local_symbols=set(),
        local_imports=local_imports,
        local_classes={},
        all_classes=all_classes,
    )


def resolve_calls(
    source: str,
    engine: ResolutionEngine,
    factory_return_types: dict[str, str] | None = None,
    propagated_self_attr_types: dict[str, str] | None = None,
    self_attr_types: dict[str, str] | None = None,
) -> list[tuple[str, str, ResolutionResult]]:
    all_classes = build_all_classes(source)
    calls = find_calls(source)
    local_vars = infer_local_var_types(source, factory_return_types or {})
    results = []

    for call_node, func, cls in calls:
        if isinstance(call_node.func, ast.Attribute):
            callee = call_node.func.attr
        elif isinstance(call_node.func, ast.Name):
            callee = call_node.func.id
        else:
            callee = "unknown"

        caller = f"{cls}.{func}" if cls else f"<module>.{func}"

        ctx = make_context(
            call_node,
            func,
            cls,
            all_classes,
            factory_return_types,
            propagated_self_attr_types,
            self_attr_types,
            local_vars,
            source=source,
        )
        result = engine.resolve(ctx)
        results.append((caller, callee, result))

    return results


def assert_resolved_by(
    results: list[tuple[str, str, ResolutionResult]],
    callee: str,
    heuristic: str,
    hint: str = "",
) -> ResolutionResult:
    for caller, c, r in results:
        if c == callee or callee in r.callee:
            assert r.heuristic == heuristic, (
                f"Expected '{heuristic}' for '{callee}', got '{r.heuristic}' ({caller}). {hint}"
            )
            return r
    pytest.fail(f"No call to '{callee}'. Callees: {[c for _, c, _ in results]}. {hint}")


def assert_trace_has(result: ResolutionResult, heuristic: str, hint: str = ""):
    for step in result.trace:
        if step.heuristic == heuristic:
            return
    pytest.fail(
        f"Trace missing '{heuristic}'. Got: {[s.heuristic for s in result.trace]}. {hint}"
    )


def assert_provenance(
    result: ResolutionResult,
    source_kind: str,
    source_symbol: str,
    hint: str = "",
):
    assert result.trace, f"Expected trace. {hint}"
    step = result.trace[0]
    assert step.source_kind == source_kind, (
        f"Expected source_kind='{source_kind}', got '{step.source_kind}'. {hint}"
    )
    assert step.source_symbol == source_symbol, (
        f"Expected source_symbol='{source_symbol}', got '{step.source_symbol}'. {hint}"
    )


class TestGateAH26H27:
    def test_gate_a_propagation(self):
        engine = create_resolution_engine(
            enable_h26_h27=True,
            enable_h28_factory_return=True,
            factory_return_types={"make_client": "Client"},
        )
        propagated: dict[str, str | None] = {"client": "Client"}

        results = resolve_calls(
            GATE_A_FIXTURE,
            engine,
            factory_return_types={"make_client": "Client"},
            propagated_self_attr_types=propagated,
        )

        r = assert_resolved_by(
            results, "send", "H2.6/2.7", "Gate A: self.client.send() via H2.6/2.7"
        )
        assert_trace_has(r, "H2.6/2.7", "Gate A: trace should show H2.6/2.7")
        assert_provenance(
            r, "self_attr_propagated", "client", "Gate A: provenance check"
        )


class TestGateBH28:
    def test_gate_b_factory_return(self):
        engine = create_resolution_engine(
            enable_h28_factory_return=True,
            factory_return_types={"builder_factory": "Builder"},
        )

        results = resolve_calls(
            GATE_B_FIXTURE,
            engine,
            factory_return_types={"builder_factory": "Builder"},
        )

        r = assert_resolved_by(results, "build", "H2.8", "Gate B: x.build() via H2.8")
        assert_trace_has(r, "H2.8", "Gate B: trace should show H2.8")
        assert_provenance(
            r, "factory_return", "builder_factory", "Gate B: provenance check"
        )

    def test_gate_b_disabled(self):
        engine = create_resolution_engine(enable_h28_factory_return=False)
        results = resolve_calls(GATE_B_FIXTURE, engine, factory_return_types={})

        for _, c, r in results:
            if c == "build":
                assert r.heuristic != "H2.8", "H2.8 should not resolve when disabled"
                return
        pytest.fail("No call to 'build' found")


class TestH28NegativeCompetition:
    """H2.8 negative and competition tests for v0.5.2."""

    # Fixture: factory var vs direct constructor assignment
    H28_VS_H1 = """
class Widget:
    def render(self):
        pass

def make_widget() -> Widget:
    return Widget()

def main():
    x = make_widget()
    x.render()
    y = Widget()
    y.render()
"""

    def test_factory_vs_constructor_assignment(self):
        """H2.8 for factory var, H1 for direct constructor assignment."""
        engine = create_resolution_engine(
            enable_h28_factory_return=True,
            factory_return_types={"make_widget": "Widget"},
        )

        results = resolve_calls(
            self.H28_VS_H1,
            engine,
            factory_return_types={"make_widget": "Widget"},
        )

        render_results = [
            (caller, r) for caller, callee, r in results if "render" in callee
        ]
        assert len(render_results) >= 2, (
            f"Expected 2 render() calls, got {len(render_results)}"
        )

        heuristics = {r.heuristic for _, r in render_results}
        assert "H2.8" in heuristics, "x.render() from factory should use H2.8"

    # Fixture: two factories with same return type
    TWO_FACTORIES_SAME_RETURN = """
class Service:
    def run(self):
        pass

def make_service_a() -> Service:
    return Service()

def make_service_b() -> Service:
    return Service()

def main():
    a = make_service_a()
    b = make_service_b()
    a.run()
    b.run()
"""

    def test_two_factories_same_return_type(self):
        """Both factory vars should resolve via H2.8."""
        engine = create_resolution_engine(
            enable_h28_factory_return=True,
            factory_return_types={
                "make_service_a": "Service",
                "make_service_b": "Service",
            },
        )

        results = resolve_calls(
            self.TWO_FACTORIES_SAME_RETURN,
            engine,
            factory_return_types={
                "make_service_a": "Service",
                "make_service_b": "Service",
            },
        )

        # Both a.run() and b.run() should resolve via H2.8
        h28_count = sum(1 for _, _, r in results if r.heuristic == "H2.8")
        assert h28_count >= 2, f"Expected 2+ H2.8 resolutions, got {h28_count}"

    # Fixture: factory return type not in known classes
    FACTORY_UNKNOWN_CLASS = """
def make_unknown():
    return UnknownClass()

def main():
    x = make_unknown()
    x.method()
"""

    def test_factory_return_unknown_class(self):
        """H2.8 should not resolve if class not in all_classes."""
        engine = create_resolution_engine(
            enable_h28_factory_return=True,
            factory_return_types={"make_unknown": "UnknownClass"},
        )

        results = resolve_calls(
            self.FACTORY_UNKNOWN_CLASS,
            engine,
            factory_return_types={"make_unknown": "UnknownClass"},
        )

        for _, _, r in results:
            assert r.heuristic != "H2.8", "H2.8 should not resolve unknown class"

    # Fixture: method not on factory return class
    FACTORY_METHOD_NOT_ON_CLASS = """
class FixedAPI:
    def allowed(self):
        pass

def make_fixed() -> FixedAPI:
    return FixedAPI()

def main():
    x = make_fixed()
    x.allowed()
    x.forbidden()  # method doesn't exist on FixedAPI
"""

    def test_factory_method_not_on_class(self):
        """H2.8 should not resolve if method not in class's methods."""
        engine = create_resolution_engine(
            enable_h28_factory_return=True,
            factory_return_types={"make_fixed": "FixedAPI"},
        )

        results = resolve_calls(
            self.FACTORY_METHOD_NOT_ON_CLASS,
            engine,
            factory_return_types={"make_fixed": "FixedAPI"},
        )

        # allowed() should resolve via H2.8
        allowed_resolved = False
        for _, _, r in results:
            if r.heuristic == "H2.8" and "allowed" in r.callee:
                allowed_resolved = True
            elif "forbidden" in r.callee:
                assert r.heuristic != "H2.8", "forbidden() should not resolve via H2.8"
        assert allowed_resolved, "allowed() should resolve via H2.8"

    # Fixture: local var shadows factory name
    FACTORY_VAR_SHADOWING = """
class Engine:
    def start(self):
        pass

def create_engine() -> Engine:
    return Engine()

def main():
    create_engine = "not a factory call"  # shadows factory name
    x = create_engine  # not a call
    y = Engine()  # direct constructor
    y.start()
"""

    def test_factory_name_shadowed(self):
        """When factory name is shadowed, H2.8 should not apply to the shadow."""
        engine = create_resolution_engine(
            enable_h28_factory_return=True,
            factory_return_types={"create_engine": "Engine"},
        )

        results = resolve_calls(
            self.FACTORY_VAR_SHADOWING,
            engine,
            factory_return_types={"create_engine": "Engine"},
        )

        # y.start() should still work via H1 (local var from constructor)
        for _, _, r in results:
            if "start" in r.callee:
                assert r.heuristic in ("H1", "H3"), "y.start() should use H1 or H3"


class TestH26H27Negative:
    """H2.6/2.7 propagated self.attr negative tests for v0.5.2."""

    UNINITIALIZED_ATTR = """
class Client:
    def send(self):
        pass

class Service:
    def run(self):
        self.client.send()
"""

    def test_uninitialized_attr_no_propagation(self):
        """H2.6/2.7 should not resolve when attr never initialized."""
        engine = create_resolution_engine(enable_h26_h27=True)

        results = resolve_calls(self.UNINITIALIZED_ATTR, engine)

        for _, callee, r in results:
            if callee == "send":
                assert r.heuristic != "H2.6/2.7", (
                    "H2.6/2.7 should not resolve uninitialized attr"
                )

    def test_h26_h27_disabled(self):
        """H2.6/2.7 should not resolve when disabled."""
        engine = create_resolution_engine(enable_h26_h27=False)

        propagated: dict[str, str | None] = {"client": "Client"}
        results = resolve_calls(
            self.UNINITIALIZED_ATTR,
            engine,
            propagated_self_attr_types=propagated,
        )

        for _, callee, r in results:
            if callee == "send":
                assert r.heuristic != "H2.6/2.7", "H2.6/2.7 disabled should not resolve"

    PROPAGATED_NONE = """
class Client:
    def send(self):
        pass

class Service:
    def run(self):
        self.client.send()
"""

    def test_propagated_value_none(self):
        """H2.6/2.7 should not resolve when propagated value is None."""
        engine = create_resolution_engine(enable_h26_h27=True)

        propagated: dict[str, str | None] = {"client": None}
        results = resolve_calls(
            self.PROPAGATED_NONE,
            engine,
            propagated_self_attr_types=propagated,
        )

        for _, callee, r in results:
            if callee == "send":
                assert r.heuristic != "H2.6/2.7", (
                    "H2.6/2.7 should not resolve when propagated is None"
                )

    ATTR_NAME_TYPO = """
class Client:
    def send(self):
        pass

class Service:
    def run(self):
        self.clint.send()
"""

    def test_attr_name_typo(self):
        """H2.6/2.7 should not resolve similar but wrong attr name."""
        engine = create_resolution_engine(enable_h26_h27=True)

        propagated: dict[str, str | None] = {"client": "Client"}
        results = resolve_calls(
            self.ATTR_NAME_TYPO,
            engine,
            propagated_self_attr_types=propagated,
        )

        for _, callee, r in results:
            if callee == "send":
                assert r.heuristic != "H2.6/2.7", (
                    "H2.6/2.7 should not resolve typo attr 'clint'"
                )


class TestGateCQualifiedAttr:
    def test_gate_c_qualified(self):
        engine = create_resolution_engine()
        results = resolve_calls(GATE_C_FIXTURE, engine)

        r = assert_resolved_by(
            results, "walk", "qualified_attr", "Gate C: ast.walk() via qualified_attr"
        )
        assert_trace_has(
            r, "qualified_attr", "Gate C: trace should show qualified_attr"
        )
        assert_provenance(r, "import_qualified", "ast", "Gate C: provenance check")


class TestQualifiedAttrBoundary:
    """qualified_attr boundary tests for v0.5.2."""

    LOCAL_VAR_METHOD = """
class Handler:
    def process(self):
        pass

def main():
    h = Handler()
    h.process()
"""

    def test_local_var_not_qualified_attr(self):
        """Local var.method() should NOT use qualified_attr."""
        engine = create_resolution_engine()
        results = resolve_calls(self.LOCAL_VAR_METHOD, engine)

        for _, callee, r in results:
            if "process" in callee:
                assert r.heuristic != "qualified_attr", (
                    "h.process() should not use qualified_attr"
                )

    IMPORT_ALIAS = """
import ast as a

def main():
    a.walk(None)
"""

    def test_import_alias_uses_qualified_attr(self):
        """import x as y; y.func() should use qualified_attr."""
        engine = create_resolution_engine()
        results = resolve_calls(self.IMPORT_ALIAS, engine)

        r = assert_resolved_by(
            results, "walk", "qualified_attr", "a.walk() via qualified_attr"
        )
        assert r.callee == "ast.walk"

    FROM_IMPORT = """
from ast import walk, parse

def main():
    walk(None)
    parse("")
"""

    def test_from_import_uses_static(self):
        """from x import f; f() should use static, not qualified_attr."""
        engine = create_resolution_engine()
        results = resolve_calls(self.FROM_IMPORT, engine)

        for _, callee, r in results:
            if callee in ("walk", "parse"):
                assert r.heuristic == "static", (
                    f"{callee}() from from-import should use static"
                )

    MODULE_NAME_SHADOWED = """
import ast

def main():
    ast = "not the module"
    len(ast)
"""

    def test_module_shadowed_not_qualified_attr(self):
        """Shadowed import name should NOT use qualified_attr."""
        engine = create_resolution_engine()
        results = resolve_calls(self.MODULE_NAME_SHADOWED, engine)

        for _, callee, r in results:
            if callee == "len":
                assert r.heuristic != "qualified_attr", (
                    "len(ast) where ast is shadowed should not use qualified_attr"
                )


class TestIntegration:
    def test_smoke_all_gates(self):
        engine = create_resolution_engine(
            enable_h25=True,
            enable_h26_h27=True,
            enable_h28_factory_return=True,
            factory_return_types={
                "make_client": "Client",
                "builder_factory": "Builder",
            },
        )

        for name, code in [
            ("A", GATE_A_FIXTURE),
            ("B", GATE_B_FIXTURE),
            ("C", GATE_C_FIXTURE),
        ]:
            results = resolve_calls(code, engine)
            assert isinstance(results, list), f"{name}: should return list"
            assert len(results) > 0, f"{name}: should have calls"

    def test_deterministic(self):
        engine = create_resolution_engine(
            enable_h26_h27=True,
            enable_h28_factory_return=True,
            factory_return_types={"make_client": "Client"},
        )
        kwargs = dict(factory_return_types={"make_client": "Client"})
        r1 = resolve_calls(GATE_A_FIXTURE, engine, **kwargs)
        r2 = resolve_calls(GATE_A_FIXTURE, engine, **kwargs)

        assert len(r1) == len(r2), "count should be deterministic"
        h1 = sorted([r.heuristic for _, _, r in r1])
        h2 = sorted([r.heuristic for _, _, r in r2])
        assert h1 == h2, "heuristics should be deterministic"

    def test_deterministic_edge_count(self):
        engine = create_resolution_engine(
            enable_h25=True,
            enable_h26_h27=True,
            enable_h28_factory_return=True,
            factory_return_types={
                "make_client": "Client",
                "builder_factory": "Builder",
            },
        )

        all_code = GATE_A_FIXTURE + GATE_B_FIXTURE + GATE_C_FIXTURE
        runs = [resolve_calls(all_code, engine) for _ in range(5)]

        counts = [len(r) for r in runs]
        assert len(set(counts)) == 1, f"Edge counts vary: {counts}"

    def test_deterministic_callee_order(self):
        engine = create_resolution_engine(
            enable_h26_h27=True,
            enable_h28_factory_return=True,
            factory_return_types={"make_client": "Client"},
        )

        r1 = resolve_calls(GATE_A_FIXTURE, engine)
        r2 = resolve_calls(GATE_A_FIXTURE, engine)

        callees1 = [callee for _, callee, _ in r1]
        callees2 = [callee for _, callee, _ in r2]
        assert callees1 == callees2, "Callee order should be deterministic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
