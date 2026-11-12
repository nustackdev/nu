"""Leaf family: a single value in a shape fabric, with no descent below it.

Forms give the slot-level surface (read, write, observe the one value); refs
bind that surface to an address. A fabric's leaves mix a value form in beside
these, so the ref itself is an operand of the value it names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from nu.lang import Literal

from .base import StructuredRef
from .dsl import Slot
from .form import SlotForm
from .rewrite import _PLACED


if TYPE_CHECKING:
    from nu.core.flows.control import IfDo
    from nu.core.reactive import OnPrimitiveChange
    from nu.domains.shape.interactions import (
        Erase,
        SetCmd,
    )
    from nu.forms import Bool


_R = TypeVar("_R")

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

    API: exists(), is_set_falsy() (from ItemForm), to(spec).
    """

    # ``Kind.slot(...)`` is typed as the ref it builds (a ``Slot`` at run
    # time), so both forms resolve to the ref class.
    @overload
    def to(self, spec: type[_R]) -> _R: ...

    @overload
    def to(self, spec: _R) -> _R: ...

    def to(self, spec: type[_R] | _R) -> _R:
        """This address as the kind ``spec`` names, so the chain goes on in that kind.

        ``grid[0, 1].to(TableRef.slot(header=cols))[1, 0]``. The
        kind is named where the child is used, never declared on the container,
        which is what lets one container hold children of different kinds.

        The result replaces this ref: same parent, same address, the class and
        props ``spec`` carries. Nothing of this ref's own kind comes along; its
        declared ``type_info`` belonged to the kind it had. Whether the store
        agrees with the new kind is the fabric's to check when it is used.

        Args:
            spec: a ref class (no props), or a slot spec ``Kind.slot(**props)``,
                which is also how a Shape-backed kind is named.

        Raises:
            TypeError: ``spec`` is neither a shape ref class nor a ``Slot``.
        """
        if isinstance(spec, Slot):
            slot = spec
        elif isinstance(spec, type) and issubclass(spec, StructuredRef):
            slot = Slot(spec)
        else:
            msg = (
                f"{type(self).__name__}.to takes a ref class or a Kind.slot(...) spec, not {spec!r}"
            )
            raise TypeError(msg)
        # A plain key was wrapped in a Literal when this ref was built; hand the
        # new one the key itself, so it is built exactly as this one was.
        address = self._children[1]
        if type(address) is Literal:
            address = address._payload["value"]
        ref = slot.create_ref(
            owner_shape=self._owner_shape,
            parent_ref=self._parent,
            address=address,
        )
        # A chain placed by ``with_parent`` stays placed: its root routes to
        # the scope it was placed under, not to its owner Shape.
        ref._payload["root_shape"] = self._root_shape  # type: ignore[attr-defined]
        if self._payload.get(_PLACED):
            ref._payload[_PLACED] = True  # type: ignore[attr-defined]
        return ref  # type: ignore[return-value]


class MutableItemRef(MutableItemForm, ItemRef):
    """Mutable leaf Ref: single typed value with write/erase.

    API: exists(), is_set_falsy(), set(v), erase() (from MutableItemForm).
    """


class ReactiveItemRef(ReactiveItemForm, MutableItemRef):
    """Reactive leaf Ref: single typed value with observation.

    API: exists(), is_set_falsy(), set(v), erase(), on_change() (from ReactiveItemForm).
    """
