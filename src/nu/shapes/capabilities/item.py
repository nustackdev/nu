# ruff: noqa: D102
"""Item-level capability bases — store, erase, exists for items in collections.

Refs ARE terms — executing a ref reads its value (via fetch/coerce).
No separate load() needed. The ref itself is the readable Nu.

ItemSettableBase: .store(value) wrapping ItemStoreCmd
ItemDeletableBase: .erase() wrapping ItemEraseCmd
ItemExistableBase: .exists(), .missing()

These bases are for refs that represent items within a collection.
The ref must implement fetch_parent(ctx) and resolve_address(ctx).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interfaces import BoolI, NoneI


if TYPE_CHECKING:
    from nu import Nu, Sentinel


__all__ = [
    "ItemDeletableBase",
    "ItemExistableBase",
    "ItemSettableBase",
]


class ItemExistableBase:
    """Base for item refs that can check existence.

    Provides exists() and missing() using ItemExistsOp/ItemMissingOp.
    """

    def exists(self) -> BoolI:
        from nu.shapes.ops.item import ItemExistsOp

        return BoolI(ItemExistsOp(self))

    def missing(self) -> BoolI:
        from nu.shapes.ops.item import ItemMissingOp

        return BoolI(ItemMissingOp(self))


class ItemSettableBase[ValueT]:
    """Base for item refs that can write a value.

    Provides store(value) using ItemStoreCmd, returning NoneI.
    """

    def store(self, value: ValueT | Sentinel | Nu[ValueT | Sentinel]) -> NoneI:
        from nu.shapes.ops.item import ItemStoreCmd
        from nu.utils import ensure_nu

        return NoneI(ItemStoreCmd(self, ensure_nu(value)))


class ItemDeletableBase:
    """Base for item refs that can be deleted.

    Provides erase() using ItemEraseCmd.
    """

    def erase(self) -> NoneI:
        from nu.shapes.ops.item import ItemEraseCmd

        return NoneI(ItemEraseCmd(self))
