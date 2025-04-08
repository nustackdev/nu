"""
Core operations for the operations framework.

This module exports the core operations that provide the basic functionality
of the operations framework.
"""

from .function import Function, handle_function_operation

__all__ = [
    "Function",
    "handle_function_operation",
]
