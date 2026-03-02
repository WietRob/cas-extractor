"""
Static and qualified resolvers — handles simple name calls and imports.
"""

import ast
from cas_extractor.resolvers.base import (
    BaseResolver,
    CallContext,
    ResolutionResult,
    ResolutionStep,
    _BUILTINS,
)


class StaticResolver(BaseResolver):
    """Resolves simple function calls to local module functions."""

    name = "static"
    priority = 10

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not isinstance(context.func_node, ast.Name):
            return None

        name = context.func_node.id

        if name in context.local_symbols:
            return ResolutionResult(
                callee=f"{context.module_qname}.{name}",
                resolution_type="static",
                heuristic=self.name,
                trace=[
                    ResolutionStep(
                        heuristic=self.name,
                        pattern_matched="local_function_call",
                        inferred_type=None,
                        reasoning=f"Found function '{name}' in local module",
                        source_kind="local_function",
                        source_symbol=name,
                        evidence_path=[f"local function {name}"],
                    )
                ],
            )

        if name in context.local_imports:
            target = context.local_imports[name]
            return ResolutionResult(
                callee=target,
                resolution_type="qualified",
                heuristic=self.name,
                trace=[
                    ResolutionStep(
                        heuristic=self.name,
                        pattern_matched="imported_call",
                        inferred_type=None,
                        reasoning=f"Found import '{name}' -> '{target}'",
                        source_kind="import_direct",
                        source_symbol=name,
                        evidence_path=[
                            f"from ... import {name}",
                            f"{name} -> {target}",
                        ],
                    )
                ],
            )

        if name in _BUILTINS:
            return ResolutionResult(
                callee="?.skip",
                resolution_type="skip",
                heuristic=self.name,
                trace=[
                    ResolutionStep(
                        heuristic=self.name,
                        pattern_matched="builtin_skip",
                        inferred_type=None,
                        reasoning=f"'{name}' is a builtin, skipping",
                        source_kind="builtin",
                        source_symbol=name,
                        evidence_path=[f"builtin {name}"],
                    )
                ],
            )

        return None


class QualifiedAttrResolver(BaseResolver):
    """Resolves qualified attribute calls like module.func (e.g., ast.walk)."""

    name = "qualified_attr"
    priority = 5

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not isinstance(context.func_node, ast.Attribute):
            return None
        if not isinstance(context.func_node.value, ast.Name):
            return None

        obj_name = context.func_node.value.id
        method_name = context.func_node.attr

        if obj_name in context.local_imports:
            target = f"{context.local_imports[obj_name]}.{method_name}"
            return ResolutionResult(
                callee=target,
                resolution_type="qualified",
                heuristic=self.name,
                trace=[
                    ResolutionStep(
                        heuristic=self.name,
                        pattern_matched="qualified_attribute_call",
                        inferred_type=None,
                        reasoning=f"Found import '{obj_name}' -> '{target}'",
                        source_kind="import_qualified",
                        source_symbol=obj_name,
                        evidence_path=[
                            f"import {obj_name}",
                            f"{obj_name}.{method_name}",
                        ],
                    )
                ],
            )

        return None


class SelfDispatchResolver(BaseResolver):
    """Resolves self.method() calls within a class."""

    name = "self_dispatch"
    priority = 70

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not isinstance(context.func_node, ast.Attribute):
            return None

        if not (
            isinstance(context.func_node.value, ast.Name)
            and context.func_node.value.id == "self"
        ):
            return None

        if context.enclosing_class is None:
            return None

        method_name = context.func_node.attr

        if method_name in context.enclosing_class.methods:
            target = f"{context.enclosing_class.qname}.{method_name}"
            return ResolutionResult(
                callee=target,
                resolution_type="self_dispatch",
                heuristic=self.name,
                trace=[
                    ResolutionStep(
                        heuristic=self.name,
                        pattern_matched="self_method_call",
                        inferred_type=context.enclosing_class.qname,
                        reasoning=f"self.{method_name}() resolves to {target}",
                        source_kind="self_dispatch",
                        source_symbol=method_name,
                        evidence_path=[f"self.{method_name}()"],
                    )
                ],
            )

        return None


class ClsDispatchResolver(BaseResolver):
    """Resolves cls.method() calls within a classmethod."""

    name = "cls_dispatch"
    priority = 80

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not isinstance(context.func_node, ast.Attribute):
            return None

        if not (
            isinstance(context.func_node.value, ast.Name)
            and context.func_node.value.id == "cls"
        ):
            return None

        if context.enclosing_class is None:
            return None

        method_name = context.func_node.attr

        if method_name in context.enclosing_class.methods:
            target = f"{context.enclosing_class.qname}.{method_name}"
            return ResolutionResult(
                callee=target,
                resolution_type="cls_dispatch",
                heuristic=self.name,
                trace=[
                    ResolutionStep(
                        heuristic=self.name,
                        pattern_matched="cls_method_call",
                        inferred_type=context.enclosing_class.qname,
                        reasoning=f"cls.{method_name}() in @classmethod resolves to {target}",
                        source_kind="cls_dispatch",
                        source_symbol=method_name,
                        evidence_path=[f"cls.{method_name}()"],
                    )
                ],
            )

        return None


class SuperDispatchResolver(BaseResolver):
    """Resolves super().method() calls."""

    name = "super_dispatch"
    priority = 90

    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        if not isinstance(context.func_node, ast.Attribute):
            return None

        func_value = context.func_node.value
        if not (
            isinstance(func_value, ast.Call)
            and isinstance(func_value.func, ast.Name)
            and func_value.func.id == "super"
        ):
            return None

        if context.enclosing_class is None:
            return None

        method_name = context.func_node.attr

        resolved = self._resolve_in_bases(
            method_name,
            context.enclosing_class,
            context.local_classes,
            context.all_classes,
            context.local_imports,
        )

        if resolved:
            base_class = resolved.rsplit(".", 1)[0]
            return ResolutionResult(
                callee=resolved,
                resolution_type="super_dispatch",
                heuristic=self.name,
                trace=[
                    ResolutionStep(
                        heuristic=self.name,
                        pattern_matched="super_method_call",
                        inferred_type=base_class,
                        reasoning=f"super().{method_name}() resolves to {resolved}",
                        source_kind="super_dispatch",
                        source_symbol=method_name,
                        evidence_path=[
                            f"super().{method_name}()",
                            f"-> {base_class}.{method_name}",
                        ],
                    )
                ],
            )

        return None

    def _resolve_in_bases(
        self, method_name, class_info, local_classes, all_classes, local_imports
    ):
        for base_name in class_info.base_names:
            base_ci = self._find_class(
                base_name, local_classes, all_classes, local_imports
            )
            if base_ci and method_name in base_ci.methods:
                return f"{base_ci.qname}.{method_name}"
        return None

    def _find_class(self, name, local_classes, all_classes, local_imports):
        if name in local_classes:
            return local_classes[name]
        if name in local_imports:
            qualified = local_imports[name]
            if qualified in all_classes:
                return all_classes[qualified]
        if name in all_classes:
            return all_classes[name]
        return None
