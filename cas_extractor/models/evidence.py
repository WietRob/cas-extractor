"""
CAS Evidence Models — internal dataclass representations.
These mirror the CAS evidence schema but are used internally
by extractors before serialization to YAML.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class EvidenceLevel(str, Enum):
    E0 = "E0"
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"


@dataclass(frozen=True)
class SourceInfo:
    repo: str
    root: str
    revision: str
    collected_at: str


@dataclass(frozen=True)
class Anchor:
    file: str
    line_start: int
    line_end: int
    qualified_symbol: str
    fingerprint: str
    git_blob_sha: Optional[str] = None


@dataclass
class SymbolEntry:
    qualified_name: str
    kind: str
    anchor: Anchor
    decorators: list[str] = field(default_factory=list)
    parameters: list[str] = field(default_factory=list)
    return_annotation: Optional[str] = None
    docstring: Optional[str] = None
    base_classes: list[str] = field(default_factory=list)


@dataclass
class ImportEntry:
    source_module: str
    target: str
    alias: Optional[str] = None
    is_from_import: bool = False
    anchor: Optional[Anchor] = None


@dataclass
class CallEntry:
    caller: str
    callee: str
    anchor: Optional[Anchor] = None
    resolution: str = "static"
    resolution_source: Optional[str] = None
    resolution_detail: Optional[dict] = None


@dataclass
class EvidenceArtifact:
    id: str
    type: str
    level: EvidenceLevel
    source: SourceInfo
    payload: dict[str, Any]
    anchors: list[dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None
