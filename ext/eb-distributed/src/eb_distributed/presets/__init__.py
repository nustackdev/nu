"""Topology presets - ready-to-use setups. Same tree runs on any preset.

# local - everything in one process
ctx = await local(runtime, NavigatorSpec())

# distributed - Ray actors across machines
ctx = await distributed(runtime, NavigatorSpec(), workers={"red": 2, "blue": 2})
"""

from .distributed import distributed
from .local import local


__all__ = [
    "distributed",
    "local",
]
