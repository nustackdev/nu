"""Abstract collection form nodes, one per type-like ``collections.abc`` layer.

A value typed only by its ABC (a ``Mapping`` that is a ``MappingProxyType``, a
``Sequence`` that is a tuple or a ``range``) gets a form here, so its surface
methods run on it like on the built-in forms. Each node mixes in the ABC
surface from ``nu.surfaces.collections.abc``:

    Collection       CollectionSurface        collections.abc.Collection
    Sequence         SequenceSurface          collections.abc.Sequence
    MutableSequence  MutableSequenceSurface   collections.abc.MutableSequence
    Mapping          MappingSurface           collections.abc.Mapping
    MutableMapping   MutableMappingSurface    collections.abc.MutableMapping
    AbstractSet      SetLikeSurface           collections.abc.Set
    MutableSet       MutableSetSurface        collections.abc.MutableSet

``AbstractSet`` follows ``typing.AbstractSet``: ``Set`` is the built-in set's
form. Capability fragments (``Sized``, ``Container``, ``Iterable``,
``Sliceable``) and the reactive tiers (a ref's, never a value's) have no form.

Results stay honest about what is known: an element or a value reads as
``Object``, a slice or a set-algebra result as the same abstract form, and a
mapping's ``keys`` / ``values`` / ``items`` as the dict views.
"""

from __future__ import annotations

import collections.abc as cabc
from typing import TYPE_CHECKING, Generic, TypeVar

from nu.lang import Form
from nu.surfaces.collections.abc import (
    CollectionSurface,
    MappingSurface,
    MutableMappingSurface,
    MutableSequenceSurface,
    MutableSetSurface,
    SequenceSurface,
    SetLikeSurface,
)


if TYPE_CHECKING:
    from nu.lang import Nu

    from .collections import DictItems, DictKeys, DictValues
    from .primitives import Object


__all__ = [
    "AbstractSet",
    "Collection",
    "Mapping",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Sequence",
]


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


def _object(operand: Nu) -> Object:
    from .primitives import Object

    return Object(operand)


class Collection(
    CollectionSurface[T, "Collection[T]", "Object"], Form[cabc.Collection[T]], Generic[T]
):
    """Any sized, iterable container, like ``collections.abc.Collection``.

    Notes:
        - Carries `len`, `contains`, `iter` and `extract`; an element reads
          as `Object`.

    Example:
        >>> nu.run(nu.Collection(frozenset({1, 2})).len())[0]
        2
    """

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object: an abstract collection declares no element form."""
        return _object(operand)


class Sequence(
    SequenceSurface[cabc.Sequence[T], T, "Sequence[T]", "Object"],
    Form[cabc.Sequence[T]],
    Generic[T],
):
    """Any ordered, indexable value, like ``collections.abc.Sequence``.

    Notes:
        - Indexing reads an `Object`; slicing reads a `Sequence` again.

    Example:
        >>> nu.run(nu.Sequence((1, 2, 3)).index(2))[0]
        1
    """

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object: an abstract sequence declares no element form."""
        return _object(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> Sequence[T]:
        """Wrap a slice as a Sequence."""
        return Sequence(operand)


class MutableSequence(
    MutableSequenceSurface[cabc.MutableSequence[T], T, "MutableSequence[T]", "Object"],
    Form[cabc.MutableSequence[T]],
    Generic[T],
):
    """Any in-place-mutable sequence, like ``collections.abc.MutableSequence``.

    Notes:
        - The mutators (`append`, `insert`, `pop`, ...) need a ref in slot 0,
          as on `List`.

    Example:
        >>> nu.run(nu.MutableSequence([3, 1, 2]).slice(0, 2))[0]
        [3, 1]
    """

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object: an abstract sequence declares no element form."""
        return _object(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> MutableSequence[T]:
        """Wrap a slice as a MutableSequence."""
        return MutableSequence(operand)


class _MappingWraps:
    """The result wraps every abstract mapping form shares: dict views and Object values."""

    def _wrap_keys_result(self, operand: Nu) -> DictKeys:
        """Wrap operand as DictKeys."""
        from .collections import DictKeys

        return DictKeys(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValues:
        """Wrap operand as DictValues."""
        from .collections import DictValues

        return DictValues(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItems:
        """Wrap operand as DictItems."""
        from .collections import DictItems

        return DictItems(operand)

    def _wrap_value_result(self, operand: Nu) -> Object:
        """Wrap operand as Object: an abstract mapping declares no value form."""
        return _object(operand)

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object: an abstract mapping declares no key form."""
        return _object(operand)


class Mapping(  # type: ignore[misc]
    _MappingWraps,
    MappingSurface[cabc.Mapping[K, V], K, V, "Mapping[K, V]", "Object"],
    Form[cabc.Mapping[K, V]],
    Generic[K, V],
):
    """Any read-only mapping, like ``collections.abc.Mapping``.

    Notes:
        - Key lookup reads an `Object`; `keys`, `values` and `items` read as
          the dict views.

    Example:
        >>> from types import MappingProxyType
        >>> nu.run(nu.Mapping(MappingProxyType({"a": 1})).get_item("a"))[0]
        1
    """


class MutableMapping(  # type: ignore[misc]
    _MappingWraps,
    MutableMappingSurface[cabc.MutableMapping[K, V], K, V, "MutableMapping[K, V]", "Object"],
    Form[cabc.MutableMapping[K, V]],
    Generic[K, V],
):
    """Any in-place-mutable mapping, like ``collections.abc.MutableMapping``.

    Notes:
        - The writes (`set_item`, `del_item`, `update`, `pop`, ...) need a ref
          in slot 0, as on `Dict`.

    Example:
        >>> nu.run(nu.MutableMapping({"a": 1, "b": 2}).len())[0]
        2
    """


class AbstractSet(
    SetLikeSurface[cabc.Set[T], T, "AbstractSet[T]", "Object"],
    Form[cabc.Set[T]],
    Generic[T],
):
    """Any set-like value, like ``collections.abc.Set`` (``typing.AbstractSet``).

    Notes:
        - Named after ``typing.AbstractSet``: ``Set`` is the built-in set's form.
        - Set algebra reads an `AbstractSet` again; an element an `Object`.

    Example:
        >>> nu.run(nu.AbstractSet(frozenset({1, 2})).union({3}))[0]
        frozenset({1, 2, 3})
    """

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object: an abstract set declares no element form."""
        return _object(operand)

    def _wrap_set_result(self, operand: Nu) -> AbstractSet[T]:
        """Wrap a set-algebra result as an AbstractSet."""
        return AbstractSet(operand)


class MutableSet(
    MutableSetSurface[cabc.MutableSet[T], T, "MutableSet[T]", "Object"],
    Form[cabc.MutableSet[T]],
    Generic[T],
):
    """Any in-place-mutable set, like ``collections.abc.MutableSet``.

    Notes:
        - The mutators (`add`, `discard`, `pop`, ...) need a ref in slot 0, as
          on `Set`.

    Example:
        >>> nu.run(nu.MutableSet({1, 2}).issubset({1, 2, 3}))[0]
        True
    """

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object: an abstract set declares no element form."""
        return _object(operand)

    def _wrap_set_result(self, operand: Nu) -> MutableSet[T]:
        """Wrap a set-algebra result as a MutableSet."""
        return MutableSet(operand)
