"""Core type definitions.

This module provides foundational types used throughout the semantics layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from redwood.types import Value


if TYPE_CHECKING:
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree
    from redwood.tree.view import BaseView

    from .core.term import RValue


# ---------------------------------------------------------
# Tree navigation types
# ---------------------------------------------------------

type PathSegment = str | int
type TuplePath = tuple[PathSegment, ...]

# ---------------------------------------------------------
# Tree node related types
# ---------------------------------------------------------

type PrimitiveNodeValue = Value

# ---------------------------------------------------------
# Reference resolution types (Refs)
# ---------------------------------------------------------


@dataclass(frozen=True)
class RefStaticSegment:
    view_type: type[BaseView]
    key: PathSegment


@dataclass(frozen=True)
class RefDynamicSegment:
    view_type: type[BaseView]
    key_expr: RValue


RefResolution = tuple[RefStaticSegment | RefDynamicSegment, ...]

# -----------------------------------------------------------
# Execution types
# -----------------------------------------------------------


@dataclass(frozen=True)
class Context:
    tree: Tree
    storage_context: ContextType
