# ruff: noqa: D102
"""Item-level capability bases — store, erase, exists for items in collections.

Refs ARE terms — executing a ref reads its value (via fetch/coerce).
No separate load() needed. The ref itself is the readable term.

ItemSettableBase: .store(value) wrapping ItemStoreCmd
ItemDeletableBase: .erase() wrapping ItemEraseCmd
ItemExistableBase: .exists(), .missing()

These bases are for refs that represent items within a collection.
The ref must implement fetch_parent(ctx) and resolve_address(ctx).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interfaces.values import BoolValue, NoneValue


if TYPE_CHECKING:
    from nu import Sentinel, Term


__all__ = [
    "ItemDeletableBase",
    "ItemExistableBase",
    "ItemSettableBase",
]


class ItemExistableBase:
    """Base for item refs that can check existence.

    Provides exists() and missing() using ItemExistsOp/ItemMissingOp.
    """

    def exists(self) -> BoolValue:
        from nu.shapes.ops.item import ItemExistsOp

        return BoolValue(ItemExistsOp(self))

    def missing(self) -> BoolValue:
        from nu.shapes.ops.item import ItemMissingOp

        return BoolValue(ItemMissingOp(self))


class ItemSettableBase[ValueT]:
    """Base for item refs that can write a value.

    Provides store(value) using ItemStoreCmd, returning NoneValue.
    """

    def store(self, value: ValueT | Sentinel | Term[ValueT | Sentinel]) -> NoneValue:
        from nu.utils import ensure_term
        from nu.shapes.ops.item import ItemStoreCmd

        return NoneValue(ItemStoreCmd(self, ensure_term(value)))


class ItemDeletableBase:
    """Base for item refs that can be deleted.

    Provides erase() using ItemEraseCmd.
    """

    def erase(self) -> NoneValue:
        from nu.shapes.ops.item import ItemEraseCmd

        return NoneValue(ItemEraseCmd(self))
