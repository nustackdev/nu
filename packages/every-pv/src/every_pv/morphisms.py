"""PV-specific morphisms.

Only TypedSetCmd remains — all collection morphisms (map, filter, reduce,
append, pop, keys, values, items, etc.) were redundant wrappers around
the Views which already implement these operations directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from pv.loc import path
from pv.traits import Assignable
from pv.view import View

from everyabc import Command, Context, Morphism, Sentinel
from everybase import ensure_term


if TYPE_CHECKING:
    from every_pv.ref import PrimitiveRef
    from everyabc import Term


__all__ = [
    "TypedSetCmd",
]


class TypedSetCmd[T](Command, Morphism[T]):
    """Set command for TypedValue that calls __to_storage__ before storing.

    PV-specific: converts typed values to storage format before writing.
    This enables custom types like DatetimeValue to define how they
    should be serialized to storage.
    """

    def __init__(
        self,
        ref: PrimitiveRef[T],
        value: Term[T | Sentinel],
    ) -> None:
        super().__init__(cast("PrimitiveRef[T]", ref), value)
        self.ref = cast("PrimitiveRef[T]", ref)
        self.value_expr = ensure_term(value)

    async def execute(self, ctx: Context) -> T:
        """Execute typed write command.

        If the value has __to_storage__, calls it to get the storable value.
        Otherwise stores the value directly.
        """
        value_path = await self.ref.resolve(ctx)
        value = await self.value_expr.execute(ctx)

        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store special values (Empty, Invalid, etc): {value}")

        if hasattr(value, "__to_storage__"):
            storage_value = value.__to_storage__()
        else:
            storage_value = value

        shape = self.ref.get_root_shape()
        root_view = ctx.get(View, shape=shape)
        parent_view, key = path.navigate_value(root_view, value_path)

        if not isinstance(parent_view, Assignable):
            raise TypeError(
                f"View {parent_view.__class__.__name__} does not implement Assignable protocol."
            )

        parent_view[key] = storage_value
        return storage_value

    def __repr__(self) -> str:
        return f"TypedSetCmd({self.ref!r}, {self.value_expr!r})"
