"""
Resolution Engine — Unified call resolution with pluggable heuristics.

v0.5.0: Refactors H1-H2.8 heuristics into a unified ResolutionEngine
with explainability support.
"""

import ast
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class CallContext:
    """Immutable context for a single call resolution."""

    func_node: ast.expr
    enclosing_func: str
    enclosing_class: "ClassInfo | None"
    local_var_types: dict[str, str]
    method_local_self_attr_types: dict[str, str]
    propagated_self_attr_types: dict[str, str | None]
    self_attr_types: dict[str, str]
    factory_return_types: dict[str, str]
    module_qname: str
    local_symbols: set[str]
    local_imports: dict[str, str]
    local_classes: dict[str, "ClassInfo"]
    all_classes: dict[str, "ClassInfo"]
    emit_unresolved_self_attr: bool = True


@dataclass
class ResolutionStep:
    """Single step in resolution explainability trace."""

    heuristic: str
    pattern_matched: str
    inferred_type: str | None
    reasoning: str


@dataclass
class ResolutionResult:
    """Result of a resolution attempt."""

    callee: str
    resolution_type: str
    heuristic: str
    trace: list[ResolutionStep] = field(default_factory=list)
    confidence: float = 1.0


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
        self.self_attr_types = self_attr_types or {}
        self.method_self_attr_summaries = method_self_attr_summaries or {}


class BaseResolver:
    """Base class for all heuristic resolvers."""

    name: str = "base"
    priority: int = 100

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        """
        Attempt to resolve the call.
        Return None if not applicable (pass through to next resolver).
        """
        raise NotImplementedError

    def can_resolve(self, context: CallContext) -> bool:
        """Quick check if this resolver might apply."""
        return True


class ResolutionEngine:
    """
    Unified resolution engine with pluggable heuristics.

    Tries each resolver in priority order until one succeeds.
    """

    def __init__(self):
        self.resolvers: list[BaseResolver] = []

    def register(self, resolver: BaseResolver) -> None:
        """Register a resolver."""
        self.resolvers.append(resolver)
        self.resolvers.sort(key=lambda r: r.priority)

    def resolve(self, context: CallContext) -> ResolutionResult:
        """
        Try each resolver in priority order until one succeeds.
        """
        for resolver in self.resolvers:
            if not resolver.enabled:
                continue

            result = resolver.try_resolve(context)
            if result is not None:
                result.heuristic = resolver.name
                return result

        # Fallback: unresolved
        return ResolutionResult(
            callee="?.unresolved",
            resolution_type="unresolved",
            heuristic="none",
        )


# Builtins to skip
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
    }
)
