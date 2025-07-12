from __future__ import annotations

from .base import BaseSpec
from .specs import ProxySpec, ResourceSpec, Spec, WrapperSpec
from .utils import get_inner_spec, get_wrapper_chain, has_wrapper_type

__all__ = [
    # Core
    "BaseSpec",
    "Spec",
    "WrapperSpec",
    # User-facing API
    "ProxySpec",
    "ResourceSpec",
    # Utility functions
    "get_inner_spec",
    "get_wrapper_chain",
    "has_wrapper_type",
]
