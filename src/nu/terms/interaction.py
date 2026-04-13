"""Interaction - base for evaluable computations.

Nu                              - the primitive
└── RValue                      - evaluable expression
    └── Interaction             - evaluable computation (structural marker)
        ├── Literal             - literal data (leaf Nu)
        └── Op                  - operation (maps inputs to outputs)
"""

from __future__ import annotations

from abc import ABC

from .nu import RValue
from .type_vars import T_co


__all__ = [
    "Interaction",
]


class Interaction(RValue[T_co], ABC):
    """Base for evaluable computations. Structural marker.

    Interaction partitions into:
    - Literal: irreducible data (leaf)
    - Op: transformation (maps inputs to outputs)
    """
