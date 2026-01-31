"""Dict substrate item refs — typed value holders in nested dicts.

ItemRef combines MutableItemRef (everyshape CRUD) with RefBase
(dict navigation). No reactivity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from every_dict.ref import RefBase
from everyabc import Value
from everyshape import MutableItemRef


if TYPE_CHECKING:
    from everyabc import Term
    from everyshape import ShapeBase


__all__ = [
    "ItemRef",
]


class ItemRef[T, ValueT: Value](
    MutableItemRef[T, ValueT],
    RefBase[T],
):
    """Dict item reference for values in nested dicts.

    Combines everyshape document model (get/set/delete/exists)
    with dict substrate (plain dict navigation).
    """

    def __init__(
        self,
        address: str | int | Term,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize item reference."""
        super().__init__(address, parent, shape)
        self._value_type = value_type
        self._value_value_type = value_value_type
