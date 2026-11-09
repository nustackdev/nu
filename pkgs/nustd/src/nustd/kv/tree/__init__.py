"""Virtuals-specific tree meta-passes: atomic wrapping."""

from .atomic import atomic
from .auto_flow_atomic import auto_flow_atomic


__all__ = [
    "atomic",
    "auto_flow_atomic",
]
