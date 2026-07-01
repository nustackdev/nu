"""virtuals-specific tree meta-passes — atomic wrapping + ref inlining.

Deferred during the v2 port: auto_flow_atomic, auto_total_atomic,
optimize_primitive_reads/writes (re-added as each lands on the v2 seam).
"""

from .auto_atomic import auto_atomic
from .inline_refs import inline_refs


__all__ = [
    "auto_atomic",
    "inline_refs",
]
