"""Virtuals-specific tree meta-passes: atomic wrapping + ref inlining."""

from .auto_flow_atomic import auto_flow_atomic
from .inline_refs import inline_refs


__all__ = [
    "auto_flow_atomic",
    "inline_refs",
]
