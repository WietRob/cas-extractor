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

    def test_gate_b_disabled(self):
        engine = create_resolution_engine(enable_h28_factory_return=False)
        results = resolve_calls(GATE_B_FIXTURE, engine, factory_return_types={})

        for _, c, r in results:
            if c == "build":
                assert r.heuristic != "H2.8", "H2.8 should not resolve when disabled"
                return
        pytest.fail("No call to 'build' found")


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
