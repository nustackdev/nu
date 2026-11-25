"""Collection form nodes.

Each node is a Span over one body that mixes in its surface from
``nu.surfaces.collections`` (``List`` = ``ListSurface`` on a ``Form[list]``).
The methods live on the surface; the node adds only its constructors, built
from the atoms in ``collections_interactions``. The dict views and
``Iterator`` live here too.
"""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView
from collections.abc import Iterator as PyIterator
from typing import TYPE_CHECKING, Generic, TypeVar

from typing_extensions import TypeVarTuple, Unpack

from nu.lang import Form
from nu.surfaces.collections import (
    DictItemsSurface,
    DictKeysSurface,
    DictSurface,
    DictValuesSurface,
    FrozenSetSurface,
    IteratorSurface,
    ListSurface,
    SetSurface,
    TupleSurface,
)

from .collections_interactions import (
    DictCreate,
    DictOf,
    FrozenSetCreate,
    FrozenSetOf,
    ListCreate,
    ListOf,
    SetCreate,
    SetOf,
    TupleCreate,
    TupleOf,
)


if TYPE_CHECKING:
    from nu.lang import Arg


__all__ = [
    "Dict",
    "DictItems",
    "DictKeys",
    "DictValues",
    "FrozenSet",
    "Iterator",
    "List",
    "Set",
    "Tuple",
]


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
Ts = TypeVarTuple("Ts")


class Dict(DictSurface[K, V], Form[dict[K, V]], Generic[K, V]):
    """Dict interface. Mutable ordered mapping, compared by value with `==` only.

    Notes:
        - Keys preserve insertion order, matching Python's `dict`.
        - No ordering comparisons (`>`, `<`, `>=`, `<=`), as on Python's
          `dict`: building one raises `TypeError`. Use `==`/`!=` for
          content comparison.
        - `is_` tests object identity. Each evaluation of a `Dict.of`/
          `Dict.create` expression builds a fresh dict, so comparing two
          separately-built dicts with `is_` is False even when their
          contents match, unlike Python's small-string interning for Str.
        - `copy`, `merge` and `merge_update` are dict-only; the rest of
          the surface comes from the shared mutable ordered-mapping base.
        - Merging is named: `merge` and `merge_update`. `&`, `|` and `>>`
          compose flows on a Dict like on every term.

    Example:
        >>> nu.run(nu.Dict.of(a=1, b=2))[0]
        {'a': 1, 'b': 2}
    """

    @classmethod
    def create(cls) -> Dict[K, V]:
        """Fresh empty dict.

        Yields:
            A new, empty dict. Never a sentinel.

        Example:
            >>> nu.run(nu.Dict.create())[0]
            {}
        """
        return cls(DictCreate())

    @classmethod
    def of(cls, **fields: Arg) -> Dict[str, V]:
        """Dict built from named field expressions.

        Args:
            fields: keyword arguments, each evaluated in the current
                context and zipped back in by name: `a=x, b=y` builds
                `{"a": <x>, "b": <y>}`. Values may be Nu expressions or
                plain literals.

        Yields:
            The assembled dict.

        Example:
            >>> nu.run(nu.Dict.of(a=1, b=2))[0]
            {'a': 1, 'b': 2}
        """
        return cls(DictOf(**fields))


class List(ListSurface[T], Form[list[T]], Generic[T]):
    """List interface. Mutable sequence + comparable.

    Notes:
        - `+` concatenates and `*` repeats, matching Python's list
          operators. There's no other arithmetic.
        - Comparison operators compare element-by-element, Python list
          ordering, and yield Bool. Chained comparisons like `a > b > c`
          do not build a single term; write them as `And(a > b, b > c)`.
        - Indexing with an out-of-range int raises at evaluation time,
          matching Python. Slicing never raises; out-of-range bounds clamp
          like Python slicing.
        - `sort` and `copy` are list-only; the rest of the mutable
          sequence surface (`set_at`, `del_at`, `append`, `extend`, ...)
          comes from the shared mutable-sequence base.
        - No subscript write/delete and no in-place `+=` / `*=`: as
          statements they drop or rebind the term. Use `set_at`, `del_at`
          and `extend`.

    Example:
        >>> nu.run(nu.List.of(1, 2) + nu.List.of(3, 4))[0]
        [1, 2, 3, 4]
    """

    @classmethod
    def create(cls) -> List[T]:
        """Yield a fresh empty list.

        Yields:
            An empty list.

        Example:
            >>> nu.run(nu.List.create())[0]
            []
        """
        return cls(ListCreate())

    @classmethod
    def of(cls, *items: Arg) -> List:
        """Yield a list from positional item expressions.

        Args:
            items: the item expressions, packed into the list in order.
                Each may be a Nu expression or a plain literal.

        Notes:
            - Sibling to `Tuple.of`, same evaluation shape, different
              wrapping.

        Yields:
            The list `[<items[0]>, <items[1]>, ...]`.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3))[0]
            [1, 2, 3]
        """
        return cls(ListOf(*items))


class Tuple(TupleSurface[Unpack[Ts]], Form[tuple[Unpack[Ts]]], Generic[Unpack[Ts]]):
    """Tuple interface. Immutable sequence + comparable.

    Notes:
        - No mutation methods: no `append`, `insert`, `pop`, `remove`. Every
          op that would change contents yields a new Tuple instead, unlike
          List which mutates in place.
        - Arity is fixed at construction; there's no way to grow or shrink
          one after `of`/`create`.
        - Indexing with an out-of-range int raises at evaluation time,
          matching Python. Slicing never raises, bounds are clamped.
        - `+` and `*` concatenate and repeat like List's, but always
          produce a new Tuple.
        - Slicing yields Tuple; `iter` and `reversed` yield a stream.

    Example:
        >>> nu.run(nu.Tuple.of(1, 2, 3))[0]
        (1, 2, 3)
    """

    @classmethod
    def create(cls) -> Tuple[Unpack[Ts]]:
        """Empty tuple.

        Yields:
            `()`.

        Example:
            >>> nu.run(nu.Tuple.create())[0]
            ()
        """
        return cls(TupleCreate())

    @classmethod
    def of(cls, *items: Arg) -> Tuple:
        """Tuple built from positional item expressions.

        Args:
            items: the expressions to evaluate and pack, in order.

        Notes:
            - Each argument is evaluated in the current context and packed:
              `Tuple.of(x, y, z)` yields `(<x>, <y>, <z>)`. Sibling to
              `List.of` and `Dict.of`.

        Yields:
            The packed tuple.

        Example:
            >>> nu.run(nu.Tuple.of(1, 2, 3))[0]
            (1, 2, 3)
        """
        return cls(TupleOf(*items))


class Set(SetSurface[T], Form[set[T]], Generic[T]):
    """Set interface. Mutable set + comparable.

    Notes:
        - Iteration order is arbitrary, matching Python's `set`. Don't rely
          on insertion order surviving a round trip.
        - `>`, `<`, `>=`, `<=` are subset/superset relations, not size
          comparisons: `a > b` means a is a proper superset of b, not that
          a has more elements. They come from the shared set base.
        - The named algebra (`union`, `issubset`, ...) and in-place
          updates (`update`, `*_update`) come from the shared set bases:
          Nu's spelling of the Set ABC operators, since `&`, `|` and `>>`
          compose flows on a set like on every term and `-` / `^` are not
          defined. Only `copy` is set-only and lives here.

    Example:
        >>> nu.run(nu.Set.of(1, 2, 3))[0]
        {1, 2, 3}
    """

    @classmethod
    def create(cls) -> Set[T]:
        """Build a fresh empty set.

        Yields:
            An empty Set.

        Example:
            >>> nu.run(nu.Set.create())[0]
            set()
        """
        return cls(SetCreate())

    @classmethod
    def of(cls, *items: Arg) -> Set:
        """Build a set from positional item expressions.

        Args:
            *items: expressions to evaluate and fold into the set, in any
                order.

        Notes:
            - Sibling to `List.of` / `Tuple.of`. Duplicate values collapse,
              same as Python `set` construction.

        Yields:
            A fresh Set holding the evaluated items.

        Example:
            >>> nu.run(nu.Set.of(1, 2, 2, 3))[0]
            {1, 2, 3}
        """
        return cls(SetOf(*items))


class FrozenSet(FrozenSetSurface[T], Form[frozenset[T]], Generic[T]):
    """FrozenSet interface. Immutable set + comparable.

    Notes:
        - Iteration order is arbitrary, matching Python's `frozenset`.
        - `>`, `<`, `>=`, `<=` are subset/superset relations, not size
          comparisons. The named algebra (`union`, `issubset`, ...) comes
          from the shared set base; only `copy` lives here. Set algebra is
          named only: `&`, `|` and `>>` compose flows.
        - No `add`/`remove`/`update`/... unlike `Set`: a FrozenSet can't be
          mutated in place.

    Example:
        >>> nu.run(nu.FrozenSet.of(1, 2, 3))[0]
        frozenset({1, 2, 3})
    """

    @classmethod
    def create(cls) -> FrozenSet[T]:
        """Build an empty frozenset.

        Yields:
            An empty FrozenSet.

        Example:
            >>> nu.run(nu.FrozenSet.create())[0]
            frozenset()
        """
        return cls(FrozenSetCreate())

    @classmethod
    def of(cls, *items: Arg) -> FrozenSet:
        """Build a frozenset from positional item expressions.

        Args:
            *items: expressions to evaluate and fold into the frozenset, in
                any order.

        Notes:
            - Sibling to `Set.of`. Duplicate values collapse, same as
              Python `frozenset` construction.

        Yields:
            A fresh FrozenSet holding the evaluated items.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2, 2, 3))[0]
            frozenset({1, 2, 3})
        """
        return cls(FrozenSetOf(*items))


class DictKeys(DictKeysSurface[K], Form[KeysView[K]], Generic[K]):
    """View of a Dict's keys, produced by `dict.keys()`.

    Notes:
        - Set-like, as Python's `KeysView` is: the subset comparisons
          (`<`, `<=`, `>`, `>=`), `isdisjoint`, and the named algebra
          (`union`, `intersection`, `difference`, ...) work on it
          directly. The named methods are Nu's spelling of the `| & - ^`
          operators, which Nu reserves or leaves undefined.
        - Lazy and live: it holds no keys of its own, it re-reads the
          backing Dict on every evaluation. Mutate the Dict and the view
          reflects it on the next `nu.run`.
        - Iterable, sized (`len()`), and supports `contains`.

    Example:
        >>> keys = nu.Dict({"a": 1, "b": 2}).keys()
        >>> nu.run(keys.len())[0]
        2
        >>> nu.run(keys.contains("a"))[0]
        True
    """


class DictValues(DictValuesSurface[V], Form[ValuesView[V]], Generic[V]):
    """View of a Dict's values, produced by `dict.values()`.

    Notes:
        - Not set-like: values can repeat and aren't required to be
          hashable, so there's no `union`/`intersection` here,
          unlike `DictKeys` and `DictItems`. Just Collection: iterable,
          sized (`len()`), and `contains`.
        - Lazy and live: it holds no values of its own, it re-reads the
          backing Dict on every evaluation. Mutate the Dict and the view
          reflects it on the next `nu.run`.
        - No `==` / `!=`: Python compares values views by identity, never
          by content, so both raise. Compare a snapshot instead:
          `values.to_list() == [...]`.

    Example:
        >>> values = nu.Dict({"a": 1, "b": 2}).values()
        >>> nu.run(values.len())[0]
        2
        >>> nu.run(values.contains(1))[0]
        True
    """


class DictItems(DictItemsSurface[K, V], Form[ItemsView[K, V]], Generic[K, V]):
    """View of a Dict's `(key, value)` pairs, produced by `dict.items()`.

    Notes:
        - Set-like, as Python's `ItemsView` is when the values are
          hashable: the subset comparisons, `isdisjoint`, and the named
          algebra (`union`, `intersection`, ...) work on it directly, Nu's
          spelling of the `| & - ^` operators.
        - Lazy and live: it holds no items of its own, it re-reads the
          backing Dict on every evaluation. Mutate the Dict and the view
          reflects it on the next `nu.run`.
        - Iterable, sized (`len()`), and supports `contains` with a
          `(key, value)` tuple.

    Example:
        >>> items = nu.Dict({"a": 1, "b": 2}).items()
        >>> nu.run(items.len())[0]
        2
        >>> nu.run(items.contains(("a", 1)))[0]
        True
    """


class Iterator(IteratorSurface[T], Form[PyIterator[T]], Generic[T]):
    """Lazy stream over another form's elements.

    Opened by `.iter()` on an IterableSurface, which wraps the source in
    a stream-shaped `Iter` term. A term of this shape produces its items one
    at a time rather than as a single value, so it sits wherever a stream
    goes: `nu.ForEachDo`, `nu.Map`, `nu.Collect`, and the itertools.

    Notes:
        - Stream-shaped, not scalar. Its surface is stream operations:
          `map`, `filter`, `sort_by`, `unique`, `reversed`, `enumerate`,
          `zip` and `flatten` stay streams; `count`, `sum`, `min`, `max`,
          `any`, `all`, `first` and `last` fold it to one value that keeps
          chaining (`.sum() > 10`); `to_list`, `to_set`, `to_tuple` and
          `sorted` drain it into a concrete collection.
        - No `==` / `!=`: an iterator has no value to compare, so both
          raise. Drain it first: `it.to_list() == [...]`.
        - An element type rides in the ``type_info`` field when the
          source declared one (a typed collection ref opened with `.iter()`).
          The item `first`/`last`/`min`/`max` read takes that type's form,
          and every op whose items are still the source's (`filter`,
          `sort_by`, `unique`, `reversed`, `to_list`, `to_set`, `sorted`)
          carries it on. `map`, `enumerate`, `zip` and `flatten` do not:
          they make new items.

    Yields:
        Its items in order, one per pull, until exhausted.

    Example:
        >>> nu.run(nu.List.of(1, 2, 3).iter().to_list())[0]
        [1, 2, 3]
    """
