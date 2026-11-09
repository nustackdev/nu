"""Leaf family: a single value in a shape fabric, with no descent below it.

Forms give the slot-level surface (read, write, observe the one value); refs
bind that surface to an address. A fabric's leaves mix a value form in beside
these, so the ref itself is an operand of the value it names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import StructuredRef
from .form import SlotForm


if TYPE_CHECKING:
    from nu.core.flows.control import IfDo
    from nu.core.reactive import OnPrimitiveChange
    from nu.domains.shape.interactions import (
        Erase,
        SetCmd,
    )
    from nu.forms import Bool


__all__ = [
    "ItemForm",
    "ItemRef",
    "MutableItemForm",
    "MutableItemRef",
    "ReactiveItemForm",
    "ReactiveItemRef",
]


class ItemForm(SlotForm):
    """Slot-level read surface for a leaf value. Ops: ``exists()``, ``is_set_falsy()``."""

    def exists(self) -> Bool:
        """Whether this slot holds a value, as a ``Bool``.

        Notes:
            - Always a bool, so it reads as one: ``.not_()``, ``.and_()``
              and ``nu.If`` take it as is.
            - Only the address is checked; a slot set to a falsy value
              (``0``, ``""``) still exists.

        Example:
            >>> class User(nu.Shape):
            ...     name = nu.StrRef.slot()
            >>> ctx = nu.Context().bind(dict, {}, User)
            >>> nu.run(User.name.exists().not_(), ctx)[0]
            True
        """
        from nu.domains.shape.interactions import Exists
        from nu.forms import Bool

        return Bool(Exists(self))

    def is_set_falsy(self) -> Bool:
        """True when this slot holds a falsy value (``False``, ``0``, ``""``, ``None``, empty).

        Notes:
            - False when the slot holds nothing, and never raises: the value
              is read only after ``exists()`` says it is there.
            - Shorthand for ``And(x.exists(), Not(x))``.
        """
        from nu.core import And, Not
        from nu.forms import Bool

        return Bool(And(self.exists(), Not(self)))


class MutableItemForm(ItemForm):
    """Slot-level write surface. Adds ``set(value)`` and ``erase()``."""

    def set(self, value: object) -> SetCmd:
        """Build a ``SetCmd``."""
        from nu.domains.shape.interactions import SetCmd

        return SetCmd(self, value)

    def erase(self) -> Erase:
        """Build an ``Erase``."""
        from nu.domains.shape.interactions import Erase

        return Erase(self)

    def init(self, value: object) -> IfDo:
        """Set ``value`` iff the leaf holds nothing yet (``exists()`` is False)."""
        from nu.core.flows.control import IfDo

        return IfDo(self.exists().not_(), self.set(value))


class ReactiveItemForm(MutableItemForm):
    """Slot-level reactive surface. Adds ``on_change()``."""

    def on_change(self) -> OnPrimitiveChange:
        """Subscribe to changes on this leaf.

        A leaf yields a scalar, not a view, so the subscription happens on the
        *parent* view's child-change channel keyed by this leaf's address.
        ``OnPrimitiveChange`` carries only the leaf ref (self); at runtime
        it calls ``ref._afetch_parent`` and ``ref._aaddress`` to resolve the
        parent view and address, then returns
        ``parent.on_child_change(address)``: one uniform path across
        substrates, no per-substrate override needed.
        """
        from nu.core.reactive import OnPrimitiveChange

        return OnPrimitiveChange(self)


class ItemRef(ItemForm, StructuredRef):
    """Leaf Ref: single typed value, no child descent.

    API: exists(), is_set_falsy() (from ItemForm).
    """


class MutableItemRef(MutableItemForm, ItemRef):
    """Mutable leaf Ref: single typed value with write/erase.

    API: exists(), is_set_falsy(), set(v), erase() (from MutableItemForm).
    """


class ReactiveItemRef(ReactiveItemForm, MutableItemRef):
    """Reactive leaf Ref: single typed value with observation.

    API: exists(), is_set_falsy(), set(v), erase(), on_change() (from ReactiveItemForm).
    """
