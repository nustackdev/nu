"""nu.reactive -- reactivity standard.

Owns the reactive contract (``ObserverProtocol`` + ``Subscription``) and the
interaction atoms (``OnChange`` / ``OnChildChange`` / ``OnChildrenChange`` /
``OnDescendantsChange`` / ``OnPrimitiveChange``).

Nu defines the standard; fabrics (nu.kv, and any future backend) bind
their observer under ``ObserverProtocol`` in ctx and match its structural
shape. Nu never depends on a concrete reactive backend.
"""

from nu.reactive.interactions import (
    OnChange,
    OnChildChange,
    OnChildrenChange,
    OnDescendantsChange,
    OnPrimitiveChange,
)
from nu.reactive.protocol import ObserverProtocol, Subscription


__all__ = [
    "ObserverProtocol",
    "OnChange",
    "OnChildChange",
    "OnChildrenChange",
    "OnDescendantsChange",
    "OnPrimitiveChange",
    "Subscription",
]
