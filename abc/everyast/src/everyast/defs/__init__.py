"""Topology node contracts and core types.

Abstract definitions for the topology programming model:
    Exec  -- base topology node
    Term  -- computation (0-cell)
    Flow  -- ordering (1-cell)
    Span  -- cohesion (2-cell)

Core types:
    Sentinel, Empty, Invalid -- special values
"""

from __future__ import annotations

from .exec import Exec
from .flow import Flow
from .sentinel import (
    EMPTY,
    INVALID,
    Empty,
    Invalid,
    Sentinel,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
)
from .span import Span
from .term import Term


__all__ = [  # noqa: RUF022
    # Topology nodes
    "Exec",
    "Term",
    "Flow",
    "Span",
    # Sentinel
    "Sentinel",
    "Empty",
    "Invalid",
    "EMPTY",
    "INVALID",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
]
