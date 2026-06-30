"""virtuals-specific tree meta-passes — atomic wrapping, ref inlining, primitive optimization."""

from .auto_atomic import auto_atomic
from .auto_flow_atomic import auto_flow_atomic
from .auto_total_atomic import auto_total_atomic
from .inline_refs import inline_refs
from .optimize_primitives import optimize_primitive_reads, optimize_primitive_writes


__all__ = [
    "auto_atomic",
    "auto_flow_atomic",
    "auto_total_atomic",
    "inline_refs",
    "optimize_primitive_reads",
    "optimize_primitive_writes",
]
