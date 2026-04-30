"""Native Query concretes.

Concrete Query atoms whose home is at the model layer (Literal, the
Reduction family). Feature-rich variants live in `nu.interactions`
during the reorg and will collapse into here progressively.
"""

from .literal import Literal
from .reduction import Collect, First, Last, Reduce


__all__ = [
    "Collect",
    "First",
    "Last",
    "Literal",
    "Reduce",
]
