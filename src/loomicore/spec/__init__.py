from __future__ import annotations

from .proxy_spec import ProxySpec
from .spec import BaseSpec, Spec, WrapperSpec
from .utils import get_inner_spec, get_wrapper_chain, has_wrapper_type

__all__ = [
    # Core
    "BaseSpec",
    "WrapperSpec",
    # User-facing API
    "Spec",
    "ProxySpec",
    # Utility functions
    "get_inner_spec",
    "get_wrapper_chain",
    "has_wrapper_type",
]
