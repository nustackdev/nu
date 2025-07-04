"""
Resource Spec Module

This implements a high-performance, type-safe spec system for Loomi with:
- attrs for frozen structs
- SHA-256 content-based hashing for deterministic keys
- Cached computations for performance
- Fluent transformation API
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .spec import BaseSpec, WrapperSpec

__all__ = [
    "get_inner_spec",
    "get_wrapper_chain",
    "has_wrapper_type",
]


def get_inner_spec(spec: "BaseSpec") -> "BaseSpec":
    """Get the innermost spec from a potentially wrapped spec."""
    current = spec
    while isinstance(current, "WrapperSpec"):
        current = current.inner_spec
    return current


def get_wrapper_chain(spec: "BaseSpec") -> "list[WrapperSpec]":
    """Get all wrapper specs from outer to inner."""
    chain = []
    current = spec
    while isinstance(current, "WrapperSpec"):
        chain.append(current)
        current = current.inner_spec
    return chain


def has_wrapper_type(spec: BaseSpec, wrapper_type: "type[WrapperSpec]") -> bool:
    """Check if spec has a specific wrapper type in its chain."""
    return any(isinstance(w, wrapper_type) for w in get_wrapper_chain(spec))
