"""What every shape collection shares: slot-level ops, and results typed by its declaration.

A collection slot declares what it holds (a value type, plus a key type for a
mapping) and that declaration rides on the ref as its ``type_info``. Every form
a collection op returns is read off that declaration: a single element reads as
the declared type's core form, and a collection result carries the declared
types on to the form it returns, so they are not lost one op later.

Pure Form mixins: no Ref or substrate knowledge, and no fabric class. Which ref
a descent lands on is the fabric's business, not this module's.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from nu.lang import Form
from nu.lang.typeinfo import TypeInfo


if TYPE_CHECKING:
    from nu.core.flows.control import IfDo
    from nu.core.reactive import (
        OnChildChange,
        OnChildrenChange,
        OnDescendantsChange,
    )
    from nu.domains.shape.interactions import (
        Erase,
        Exists,
        Extract,
        Missing,
        SetCmd,
    )


__all__ = [
    "CollectionForm",
    "MutableCollectionForm",
    "ReactiveCollectionForm",
]


_UNDECLARED = TypeInfo.any()

_F = TypeVar("_F", bound=Form)


def form_of(declared: TypeInfo | None) -> type[Form]:
    """The core form a declared type reads as; ``Object`` when nothing is declared."""
    return (declared or _UNDECLARED).to_form()


def holding(
    result: _F, py_type: type, *, key: TypeInfo | None = None, elem: TypeInfo | None = None
) -> _F:
    """``result`` carrying the declared key and element types, so its own ops stay typed."""
    if key is not None or elem is not None:
        result._payload["type_info"] = TypeInfo(py_type, key=key, elem=elem)  # type: ignore[attr-defined]
    return result


class CollectionForm(Form):
    """Shape collection Form. Ops: ``exists()``, ``missing()``, ``extract()``."""

    @property
    def _declared(self) -> TypeInfo:
        """What the slot declared this collection holds; nothing known when undeclared."""
        return self._payload.get("type_info") or _UNDECLARED  # type: ignore[attr-defined, no-any-return]

    def exists(self) -> Exists:
        """Build an ``Exists`` query."""
        from nu.domains.shape.interactions import Exists

        return Exists(self)

    def missing(self) -> Missing:
        """Build a ``Missing`` query."""
        from nu.domains.shape.interactions import Missing

        return Missing(self)

    def extract(self) -> Extract:
        """Build an ``Extract`` query."""
        from nu.domains.shape.interactions import Extract

        return Extract(self)


class MutableCollectionForm(CollectionForm):
    """Mutable shape collection Form. Adds ``set(value)`` and ``erase()``."""

    def set(self, value: object) -> SetCmd:
        """Build a ``SetCmd``."""
        from nu.domains.shape.interactions import SetCmd

        return SetCmd(self, value)

    def erase(self) -> Erase:
        """Build an ``Erase``."""
        from nu.domains.shape.interactions import Erase

        return Erase(self)

    def init(self, value: object) -> IfDo:
        """Set ``value`` iff the collection is currently missing."""
        from nu.core.flows.control import IfDo

        return IfDo(self.missing(), self.set(value))


class ReactiveCollectionForm(MutableCollectionForm):
    """Reactive shape collection Form. Adds tree-aware observation.

    Ops:
        on_child_change(address)         -> OnChildChange
        on_children_change()             -> OnChildrenChange
        on_descendants_change(*pattern)  -> OnDescendantsChange

    ``on_change()`` (observe self) is intentionally absent. It is generic and
    supplied by the generic ``ReactiveXxxForm`` tier via MRO.
    """

    def on_child_change(self, address: object) -> OnChildChange:
        """Observe changes at a specific child address."""
        from nu.core.reactive import OnChildChange

        return OnChildChange(self, address)

    def on_children_change(self) -> OnChildrenChange:
        """Observe changes across all direct children."""
        from nu.core.reactive import OnChildrenChange

        return OnChildrenChange(self)

    def on_descendants_change(self, *pattern: object) -> OnDescendantsChange:
        """Observe changes across descendants matching ``pattern``."""
        from nu.core.reactive import OnDescendantsChange

        return OnDescendantsChange(self, *pattern)
