"""virtuals-specific queries — unsafe primitive reads for virtuals substrate."""

from .collection import ScanPrimitivesUnsafe
from .item import ItemPrimitiveGetUnsafe


__all__ = [
    "ItemPrimitiveGetUnsafe",
    "ScanPrimitivesUnsafe",
]
