"""Shape-model capabilities — item CRUD, collection ops, reactive observation.

These capabilities are specific to the shape/document model (refs with
fetch/fetch_parent/resolve_address). Pure pythonic capabilities live in
everybase.capabilities.

PV-specific capabilities (CollectionInitializableBase, CollectionScanPrimitivesBase,
CollectionClearPrimitivesBase, ItemPrimitive*Base) live in eb_virtuals.capabilities.
"""

from .collection import (
    CollectionDeletableBase,
    CollectionExistableBase,
    CollectionSettableBase,
)
from .item import (
    ItemDeletableBase,
    ItemExistableBase,
    ItemSettableBase,
)

# from .loc import (
#     LocationDeletableProtocol,
#     LocationExistableProtocol,
#     LocationGettableProtocol,
#     LocationObservableProtocol,
#     LocationSettableProtocol,
# )
from .reactive import (
    PrimitiveObservableBase,
    ViewObservableBase,
)


__all__ = [  # noqa: RUF022
    # Item access bases
    "ItemDeletableBase",
    "ItemExistableBase",
    "ItemSettableBase",
    # Collection bases
    "CollectionDeletableBase",
    "CollectionExistableBase",
    "CollectionSettableBase",
    # Reactive bases
    "PrimitiveObservableBase",
    "ViewObservableBase",
]
