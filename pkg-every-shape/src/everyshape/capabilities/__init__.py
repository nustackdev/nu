"""Shape-model capabilities — item CRUD, collection ops, reactive observation.

These capabilities are specific to the shape/document model (refs with
fetch/fetch_parent/resolve_address). Pure pythonic capabilities live in
everybase.capabilities.
"""

from .collection import (
    CollectionClearableBase,
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionStorableBase,
)
from .item import (
    ItemDeletableBase,
    ItemExistableBase,
    ItemGettableBase,
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
    "ItemGettableBase",
    "ItemSettableBase",
    # Collection bases
    "CollectionClearableBase",
    "CollectionExistableBase",
    "CollectionExtractableBase",
    "CollectionStorableBase",
    # Reactive bases
    "PrimitiveObservableBase",
    "ViewObservableBase",
]
