"""Sources: the ``On*`` queries that open a ``Subscription``.

``on`` holds the single-view sources (``OnChange``, ``OnChildChange``,
``OnChildrenChange``, ``OnDescendantsChange``, ``OnPrimitiveChange``); ``any``
holds ``OnAny``, one subscription over several.
"""

from .any import OnAny
from .on import (
    OnChange,
    OnChildChange,
    OnChildrenChange,
    OnDescendantsChange,
    OnPrimitiveChange,
)


__all__ = [
    "OnAny",
    "OnChange",
    "OnChildChange",
    "OnChildrenChange",
    "OnDescendantsChange",
    "OnPrimitiveChange",
]
