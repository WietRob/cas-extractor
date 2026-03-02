"""
Local variable and self-attribute resolvers — H1, H2, H2.5, H2.6/2.7, H2.8.
"""

import ast
from cas_extractor.resolvers.base import (
    BaseResolver,
    CallContext,
    ResolutionResult,
    ResolutionStep,
)


class LocalVarResolver(BaseResolver):
    """H1: Resolves x.method() where x = ClassName() in same scope."""

    name = "H1"
    priority = 15

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not isinstance(context.func_node, ast.Attribute):
            return None

        if not isinstance(context.func_node.value, ast.Name):
            return None

        obj_name = context.func_node.value.id
        method_name = context.func_node.attr

        if obj_name not in context.local_var_types:
            return None

        class_qname = context.local_var_types[obj_name]
        ci = context.all_classes.get(class_qname)

        if ci is None or method_name not in ci.methods:
            return None

        target = f"{ci.qname}.{method_name}"
        return ResolutionResult(
            callee=target,
            resolution_type="local_var_dispatch",
            heuristic=self.name,
            trace=[
                ResolutionStep(
                    heuristic=self.name,
                    pattern_matched="local_var_assignment",
                    inferred_type=class_qname,
                    reasoning=f"Found local var '{obj_name}' = {class_qname}() in same scope",
                )
            ],
        )


class ConstructorResolver(BaseResolver):
    """H3: Resolves ClassName().method() where ClassName is a known class."""

    name = "H3"
    priority = 60

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not isinstance(context.func_node, ast.Attribute):
            return None

        if not isinstance(context.func_node.value, ast.Call):
            return None

        call_node = context.func_node.value
        if not isinstance(call_node.func, ast.Name):
            return None

        class_name = call_node.func.id
        method_name = context.func_node.attr

        if class_name in context.local_classes:
            ci = context.local_classes[class_name]
            if method_name in ci.methods:
                target = f"{ci.qname}.{method_name}"
                return ResolutionResult(
                    callee=target,
                    resolution_type="ctor_dispatch",
                    heuristic=self.name,
                    trace=[
                        ResolutionStep(
                            heuristic=self.name,
                            pattern_matched="constructor_chain",
                            inferred_type=ci.qname,
                            reasoning=f"Found ClassName() = {ci.qname}()",
                        )
                    ],
                )

        if class_name in context.local_imports:
            qualified = context.local_imports[class_name]
            if qualified in context.all_classes:
                ci = context.all_classes[qualified]
                if method_name in ci.methods:
                    target = f"{ci.qname}.{method_name}"
                    return ResolutionResult(
                        callee=target,
                        resolution_type="ctor_dispatch",
                        heuristic=self.name,
                        trace=[
                            ResolutionStep(
                                heuristic=self.name,
                                pattern_matched="constructor_chain_imported",
                                inferred_type=ci.qname,
                                reasoning=f"Found imported class {class_name} -> {ci.qname}",
                            )
                        ],
                    )

        return None


class ClassInitSelfAttrResolver(BaseResolver):
    """H2: Resolves self.attr.method() where self.attr = ClassName() in __init__."""

    name = "H2"
    priority = 50

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not self._is_self_attr_call(context):
            return None

        attr_name = context.func_node.value.attr
        method_name = context.func_node.attr

        if context.enclosing_class is None:
            return None

        if attr_name not in context.enclosing_class.self_attr_types:
            if not context.emit_unresolved_self_attr:
                return ResolutionResult(
                    callee="?.skip",
                    resolution_type="skip",
                    heuristic=self.name,
                    trace=[],
                )
            return None

        class_qname = context.enclosing_class.self_attr_types[attr_name]
        ci = context.all_classes.get(class_qname)

        if ci is None or method_name not in ci.methods:
            if not context.emit_unresolved_self_attr:
                return ResolutionResult(
                    callee="?.skip",
                    resolution_type="skip",
                    heuristic=self.name,
                    trace=[],
                )
            return None

        target = f"{ci.qname}.{method_name}"
        return ResolutionResult(
            callee=target,
            resolution_type="self_attr_dispatch",
            heuristic=self.name,
            trace=[
                ResolutionStep(
                    heuristic=self.name,
                    pattern_matched="self_attr_init",
                    inferred_type=class_qname,
                    reasoning=f"Found self.{attr_name} = {class_qname}() in __init__",
                )
            ],
        )

    def _is_self_attr_call(self, context: CallContext) -> bool:
        if not isinstance(context.func_node, ast.Attribute):
            return False
        if not isinstance(context.func_node.value, ast.Attribute):
            return False
        if not isinstance(context.func_node.value.value, ast.Name):
            return False
        return context.func_node.value.value.id == "self"


class MethodLocalSelfAttrResolver(BaseResolver):
    """H2.5: Resolves self.attr.method() where attr assigned in same method."""

    name = "H2.5"
    priority = 20

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not self.enabled:
            return None

        if not self._is_self_attr_call(context):
            return None

        attr_name = context.func_node.value.attr
        method_name = context.func_node.attr

        if context.enclosing_class is None:
            return None

        if attr_name not in context.method_local_self_attr_types:
            return None

        class_qname = context.method_local_self_attr_types[attr_name]
        ci = context.all_classes.get(class_qname)

        if ci is None or method_name not in ci.methods:
            return None

        target = f"{ci.qname}.{method_name}"
        return ResolutionResult(
            callee=target,
            resolution_type="self_attr_dispatch",
            heuristic=self.name,
            trace=[
                ResolutionStep(
                    heuristic=self.name,
                    pattern_matched="self_attr_method_local",
                    inferred_type=class_qname,
                    reasoning=f"Found self.{attr_name} = {class_qname}() in same method",
                )
            ],
        )

    def _is_self_attr_call(self, context: CallContext) -> bool:
        if not isinstance(context.func_node, ast.Attribute):
            return False
        if not isinstance(context.func_node.value, ast.Attribute):
            return False
        if not isinstance(context.func_node.value.value, ast.Name):
            return False
        return context.func_node.value.value.id == "self"


class PropagatedSelfAttrResolver(BaseResolver):
    """H2.6/H2.7: Resolves self.attr.method() via helper chain propagation."""

    name = "H2.6/2.7"
    priority = 30

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not self.enabled:
            return None

        if not self._is_self_attr_call(context):
            return None

        attr_name = context.func_node.value.attr
        method_name = context.func_node.attr

        if context.enclosing_class is None:
            return None

        if attr_name not in context.propagated_self_attr_types:
            return None

        class_qname = context.propagated_self_attr_types[attr_name]

        if class_qname is None:
            return None

        ci = context.all_classes.get(class_qname)

        if ci is None or method_name not in ci.methods:
            return None

        target = f"{ci.qname}.{method_name}"
        return ResolutionResult(
            callee=target,
            resolution_type="self_attr_dispatch",
            heuristic=self.name,
            trace=[
                ResolutionStep(
                    heuristic=self.name,
                    pattern_matched="self_attr_propagated",
                    inferred_type=class_qname,
                    reasoning=f"Found self.{attr_name} = {class_qname}() via helper chain propagation",
                )
            ],
        )

    def _is_self_attr_call(self, context: CallContext) -> bool:
        if not isinstance(context.func_node, ast.Attribute):
            return False
        if not isinstance(context.func_node.value, ast.Attribute):
            return False
        if not isinstance(context.func_node.value.value, ast.Name):
            return False
        return context.func_node.value.value.id == "self"


class UnresolvedSelfAttrResolver(BaseResolver):
    """Handles unresolved self.attr.method() when emit_unresolved_self_attr is False."""

    name = "H2_unresolved"
    priority = 100

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not self._is_self_attr_call(context):
            return None

        if context.emit_unresolved_self_attr:
            return None

        attr_name = context.func_node.value.attr
        method_name = context.func_node.attr

        return ResolutionResult(
            callee="?.skip",
            resolution_type="skip",
            heuristic=self.name,
            trace=[
                ResolutionStep(
                    heuristic=self.name,
                    pattern_matched="self_attr_unresolved_skipped",
                    inferred_type=None,
                    reasoning="emit_unresolved_self_attr=False, skipping unresolved",
                )
            ],
        )

    def _is_self_attr_call(self, context: CallContext) -> bool:
        if not isinstance(context.func_node, ast.Attribute):
            return False
        if not isinstance(context.func_node.value, ast.Attribute):
            return False
        if not isinstance(context.func_node.value.value, ast.Name):
            return False
        return context.func_node.value.value.id == "self"


class FactoryReturnResolver(BaseResolver):
    """H2.8: Resolves x.method() where x = factory() and factory returns ClassName()."""

    name = "H2.8"
    priority = 1

    def __init__(
        self, enabled: bool = True, factory_return_types: dict[str, str] | None = None
    ):
        super().__init__(enabled)
        self.factory_return_types = factory_return_types or {}

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not self.enabled:
            return None

        if not isinstance(context.func_node, ast.Attribute):
            return None

        if not isinstance(context.func_node.value, ast.Name):
            return None

        obj_name = context.func_node.value.id
        method_name = context.func_node.attr

        class_qname = None
        if obj_name in context.local_var_types:
            class_qname = context.local_var_types[obj_name]
        elif obj_name in context.factory_return_types:
            class_qname = context.factory_return_types[obj_name]

        if not class_qname:
            return None

        if class_qname not in context.factory_return_types.values():
            return None

        ci = context.all_classes.get(class_qname)

        if ci is None or method_name not in ci.methods:
            return None

        target = f"{ci.qname}.{method_name}"
        return ResolutionResult(
            callee=target,
            resolution_type="factory_return_dispatch",
            heuristic=self.name,
            trace=[
                ResolutionStep(
                    heuristic=self.name,
                    pattern_matched="factory_return",
                    inferred_type=class_qname,
                    reasoning=f"Found factory return type '{class_qname}' for variable '{obj_name}'",
                )
            ],
        )
