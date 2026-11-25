"""What every shape collection shares: slot-level ops, and results typed by its declaration.

A collection slot declares what it holds (a value type, plus a key type for a
mapping) and that declaration rides on the ref as its ``type_info``. Every form
a collection op returns is read off that declaration: a single element reads as
the declared type's core form, and a collection result carries the declared
types on to the form it returns, so they are not lost one op later.

Pure surfaces: no Ref or substrate knowledge, and no fabric class. Which ref
a descent lands on is the fabric's business, not this module's.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang.typeinfo import TypeInfo

from .form import SlotSurface


if TYPE_CHECKING:
    from nu.core.flows.control import IfDo
    from nu.core.reactive import (
        OnChange,
        OnChildChange,
        OnChildrenChange,
        OnDescendantsChange,
    )
    from nu.domains.shape.interactions import (
        Erase,
        SetCmd,
    )
    from nu.forms import Bool
    from nu.lang import Form, ScalarQuery


__all__ = [
    "CollectionSurface",
    "MutableCollectionSurface",
    "ReactiveCollectionSurface",
    "holds",
]


_UNDECLARED = TypeInfo.any()


def form_of(declared: TypeInfo | None) -> type[Form]:
    """The core form a declared type reads as; ``Object`` when nothing is declared."""
    return (declared or _UNDECLARED).to_form()


def holds(
    py_type: type, *, key: TypeInfo | None = None, elem: TypeInfo | None = None
) -> TypeInfo | None:
    """The ``type_info`` a collection result carries so its own ops stay typed.

    None when neither the key nor the element type is declared. Passed to the
    result form's constructor: ``List(operand, type_info=holds(list, elem=e))``.
    """
    if key is None and elem is None:
        return None
    return TypeInfo(py_type, key=key, elem=elem)


class CollectionSurface(SlotSurface):
    """Shape collection surface. Ops: ``exists()``, ``is_set_falsy()``, ``extract()``."""

    @property
    def _declared(self) -> TypeInfo:
        """What the slot declared this collection holds; nothing known when undeclared."""
        return self._type_info or _UNDECLARED  # type: ignore[attr-defined, no-any-return]

    def exists(self) -> Bool:
        """Whether this collection slot holds a value, as a ``Bool``.

        Notes:
            - Always a bool, so it reads as one: ``.not_()``, ``.and_()``
              and ``nu.If`` take it as is.
            - Only the address is checked; a slot set to an empty
              collection still exists.

        Example:
            >>> class User(nu.Shape):
            ...     tags = nu.ListRef.slot(str)
            >>> ctx = nu.Context().bind(dict, {}, User)
            >>> nu.run(User.tags.exists().not_(), ctx)[0]
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

    def extract(self) -> ScalarQuery:
        """Build an ``Extract`` query. A fabric may answer with its own whole-subtree read."""
        from nu.domains.shape.interactions import Extract

        return Extract(self)


class MutableCollectionSurface(CollectionSurface):
    """Mutable shape collection surface. Adds ``set(value)`` and ``erase()``."""

    def set(self, value: object) -> SetCmd:
        """Build a ``SetCmd``."""
        from nu.domains.shape.interactions import SetCmd

        return SetCmd(self, value)

    def erase(self) -> Erase:
        """Build an ``Erase``."""
        from nu.domains.shape.interactions import Erase

        return Erase(self)

    def init(self, value: object) -> IfDo:
        """Set ``value`` iff the collection holds nothing yet (``exists()`` is False)."""
        from nu.core.flows.control import IfDo

        return IfDo(self.exists().not_(), self.set(value))


class ReactiveCollectionSurface(MutableCollectionSurface):
    """Reactive shape collection surface. Adds observation of the slot and its subtree.

    Ops:
        on_change()                      -> OnChange
        on_child_change(address)         -> OnChildChange
        on_children_change()             -> OnChildrenChange
        on_descendants_change(*pattern)  -> OnDescendantsChange

    Watching is a capability of the slot, not of the value it holds, so it
    lives here for every row: a tuple or frozenset slot is watched like a
    list slot, though its value never changes in place.
    """

    def on_change(self) -> OnChange:
        """Observe any write to this slot, whichever op made it."""
        from nu.core.reactive import OnChange

        return OnChange(self)

    def on_child_change(self, address: object) -> OnChildChange:
        """Observe writes at one child's own address; for its subtree use ``on_descendants_change``."""
        from nu.core.reactive import OnChildChange

        return OnChildChange(self, address)

    def on_children_change(self) -> OnChildrenChange:
        """Observe writes at the direct children only; for subtrees use ``on_descendants_change``."""
        from nu.core.reactive import OnChildrenChange

        return OnChildrenChange(self)

    def on_descendants_change(self, *pattern: object) -> OnDescendantsChange:
        """Observe changes across descendants matching ``pattern``."""
        from nu.core.reactive import OnDescendantsChange

        return OnDescendantsChange(self, *pattern)
