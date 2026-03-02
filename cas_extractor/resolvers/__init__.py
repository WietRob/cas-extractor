"""
Resolution Engine — Unified call resolution with pluggable heuristics.

Exports:
    - ResolutionEngine: Main resolution engine
    - CallContext: Context for resolution
    - ResolutionResult: Result with trace
    - BaseResolver: Base class for resolvers
"""

from cas_extractor.resolvers.base import (
    ResolutionEngine,
    CallContext,
    ResolutionResult,
    ResolutionStep,
    BaseResolver,
    ClassInfo,
)

from cas_extractor.resolvers.static import (
    StaticResolver,
    QualifiedAttrResolver,
    SelfDispatchResolver,
    ClsDispatchResolver,
    SuperDispatchResolver,
)

from cas_extractor.resolvers.heuristics import (
    LocalVarResolver,
    ConstructorResolver,
    ClassInitSelfAttrResolver,
    MethodLocalSelfAttrResolver,
    PropagatedSelfAttrResolver,
    UnresolvedSelfAttrResolver,
    FactoryReturnResolver,
)


def create_resolution_engine(
    enable_h25: bool = False,
    enable_h26_h27: bool = False,
    enable_h28_factory_return: bool = False,
    factory_return_types: dict[str, str] | None = None,
) -> ResolutionEngine:
    """Factory function to create configured resolution engine."""
    engine = ResolutionEngine()

    engine.register(QualifiedAttrResolver())
    engine.register(StaticResolver())
    engine.register(LocalVarResolver())
    engine.register(MethodLocalSelfAttrResolver(enabled=enable_h25))
    engine.register(PropagatedSelfAttrResolver(enabled=enable_h26_h27))
    engine.register(
        FactoryReturnResolver(
            enabled=enable_h28_factory_return, factory_return_types=factory_return_types
        )
    )
    engine.register(ClassInitSelfAttrResolver())
    engine.register(ConstructorResolver())
    engine.register(SelfDispatchResolver())
    engine.register(ClsDispatchResolver())
    engine.register(SuperDispatchResolver())
    engine.register(UnresolvedSelfAttrResolver())

    return engine
