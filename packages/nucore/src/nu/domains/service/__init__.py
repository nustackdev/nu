"""Nu service domain: flat/capability DSL, sibling of shape."""

from __future__ import annotations

from .dsl import Method, MethodDescriptor, Service, ServiceMeta
from .refs import MethodRef


__all__ = [
    "Method",
    "MethodDescriptor",
    "MethodRef",
    "Service",
    "ServiceMeta",
]
