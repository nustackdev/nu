"""Nu - the user-facing base class for every Nu construct.

A thin subclass of ``Term``. Every concrete Nu sort (``Ref``, ``Interaction``,
``ScalarQuery``, ``StreamQuery``, ...) descends from ``Nu``; users annotate
their applications with ``Nu`` rather than reaching for the engine-level
``Term``. Engine machinery still operates on ``Term`` and accepts any ``Nu``
transparently. What this class adds is the operator surface every term shares:
flow composition, and the dunders Python forces to plain values (``bool()``,
``in``, ``len()``, iteration, and ``==`` on a term with no Form), which raise
with a hint.

Typical use::

    def my_app() -> Nu:
        return Add(Literal(1), Literal(2))

Custom atoms extend ``Nu`` (or one of its sort subclasses); ``Term`` is reserved
for engine-level work. ``Nu`` itself is abstract: it declares no ``sort`` /
``cardinality`` / effect attributes, so a plain ``Nu(...)`` cannot
pass schema resolution. The algebraic identity element of the tree is
``Span`` (and its sub-shapes ``Bracket`` / ``Policy``), which carries the
TRANSPARENT cardinality and the rest of the forwarding machinery.

``Nu`` is generic over ``V_co``, the yield type, covariant since ``V``
appears only in output positions. The ``R`` parameter of ``Term`` is fixed
to ``Runtime`` at this layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NoReturn, TypeVar, cast

from nu.engine import Term
from nu.lang.runtime import Runtime


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ["Nu"]


V_co = TypeVar("V_co", covariant=True)


class Nu(Term[Runtime, V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """The user-facing base for every Nu construct.

    A tagged ``Term`` carrying the language's ``Runtime`` binding and a
    yield type ``V_co``. Abstract: concrete sorts declare the structural,
    effect, cardinality, and async attributes the engine requires.
    """

    def __init__(self, *children: object) -> None:
        # Auto-wrap any non-Nu child as Literal so `Add(1, 2)` reads the same as
        # `Add(Literal(1), Literal(2))`. The import is lazy because `Literal`
        # subclasses `ScalarQuery`, which subclasses this class - a real cycle,
        # not a layering choice. Skipped entirely when every child is already a
        # Nu (the common case, and what lets a childless Ref - e.g. the stdio
        # singletons - construct during import).
        if all(isinstance(c, Nu) for c in children):
            wrapped = cast("tuple[Nu, ...]", children)
        else:
            from nu.lang.literal import Literal

            wrapped = tuple(c if isinstance(c, Nu) else Literal(c) for c in children)
        super().__init__(*wrapped)

    # --- display --------------------------------------------------------
    #
    # Both forms come from ``nu.lang.render`` and nothing else: no Nu subclass
    # defines its own ``__repr__`` / ``__str__``, so every atom renders the same
    # way and a new one needs no display code. Lazy imports because ``render``
    # imports the kind taxonomy, which imports this module.

    def __str__(self) -> str:
        """The tree as a plain box-tree, one node per line.

        Plain, never ANSI: piping to a file must not carry escape codes. For
        color at a REPL, call ``nu.render_str(term)`` directly.
        """
        from nu.lang.render import render_str

        return render_str(self, as_="plain")

    def __repr__(self) -> str:
        """The one-line constructor form, ``Add(1, 2)``."""
        from nu.lang.render import render_repr

        return render_repr(self)

    # --- composition operators ------------------------------------------
    #
    # Sugar for the Strategy flows: ``a >> b`` is ``Sequential(a, b)``,
    # ``a | b`` is ``Parallel(a, b)``, ``a & b`` is ``Race(a, b)``. Lazy
    # imports keep the lang base free of a flows dependency (flows import
    # from lang). Each call builds a fresh two-child Strategy; chains nest
    # left-to-right (``a >> b >> c`` is ``Sequential(Sequential(a, b), c)``),
    # which the associativity attribute lets the engine flatten.
    #
    # A Form whose Python type gives one of these operators a meaning
    # overrides it with that meaning (Int ``& | >>`` are bitwise, Bool
    # ``& |`` are logical, Set ``& |`` are set algebra, Dict ``|`` merges).
    # Everywhere else they stay flow composition.

    def __rshift__(self, other: object) -> Nu:
        from nu.core.flows import Sequential

        return Sequential(self, other)

    def __or__(self, other: object) -> Nu:
        from nu.core.flows import Parallel

        return Parallel(self, other)

    def __and__(self, other: object) -> Nu:
        from nu.core.flows import Race

        return Race(self, other)

    # --- equality -------------------------------------------------------
    #
    # ``==`` / ``!=`` never answer with a Python bool about the Python
    # objects. A Form (and a Ref carrying one) overrides both to build an
    # ``Eq`` / ``Ne`` term over the values: ``x == 3`` inside a program means
    # "compare what x yields". A bare term (an interaction, a flow, a Ref
    # with no Form) has no value surface, so both raise here instead of
    # quietly building comparisons. Identity stays ``is``; structural
    # comparison of two trees is ``nu.tree.equal``. Hashing stays identity
    # based, so terms still work as dict keys and set members (Python checks
    # ``is`` before ``==``, and distinct live objects never share an
    # identity hash).
    #
    # Python drops ``__hash__`` on any class that defines ``__eq__`` without
    # it; ``__init_subclass__`` puts back the nearest real hash in the MRO
    # once, here, so no Form has to repeat it. For a term that is identity
    # hashing; a class that also carries a builtin's value hash keeps it.

    __hash__ = object.__hash__

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__hash__ is None:  # type: ignore[comparison-overlap]
            cls.__hash__ = _inherited_hash(cls)  # type: ignore[method-assign]

    # Typed as yielding a term, the contract every override keeps: a Form
    # returns its ``Bool``, and this base never returns at all.
    def __eq__(self, other: object) -> Nu:  # type: ignore[override]
        raise TypeError(_eq_hint(self, "=="))

    def __ne__(self, other: object) -> Nu:  # type: ignore[override]
        raise TypeError(_eq_hint(self, "!="))

    # --- blocked protocol dunders ---------------------------------------
    #
    # Python forces ``bool()``, ``in`` and ``len()`` to return plain values,
    # so on a term they can only answer about the Python object, never about
    # the value the term yields at run time. That silent answer is always a
    # bug in a program under construction, so each raises with the explicit
    # spelling instead. No Form overrides these. Working with a term as a
    # Python object (its children, its size) goes through ``nu.tree``.

    def __bool__(self) -> bool:
        raise TypeError(_bool_hint(self))

    def __contains__(self, item: object) -> bool:
        raise TypeError(_contains_hint(self))

    def __len__(self) -> int:
        raise TypeError(_len_hint(self))

    # Python iteration over a term (``for``, ``list()``, unpacking, ``next()``)
    # would loop at build time over a program that has not run. Without this
    # block, ``__getitem__`` on a Form makes Python fall back to indexing
    # 0, 1, 2, ... forever. Nu iterates with its own streams and flows.

    def __iter__(self) -> NoReturn:
        raise TypeError(_iter_hint(self))

    def __next__(self) -> NoReturn:
        raise TypeError(_iter_hint(self))


def _inherited_hash(cls: type) -> Callable[[object], int]:
    """The first real ``__hash__`` up ``cls``'s MRO, skipping the dropped ones."""
    for base in cls.__mro__[1:]:
        found = base.__dict__.get("__hash__")
        if found is not None:
            return found  # type: ignore[no-any-return]
    return object.__hash__


def _eq_hint(term: Nu, op: str) -> str:
    """The TypeError message for ``term == x`` on a term with no Form."""
    name = type(term).__name__
    return (
        f"`t {op} x` on a bare term ({name}) can't build a comparison: wrap it in a "
        f"form to compare values, nu.Object(t) {op} x. Compare trees with "
        f"nu.tree.equal(a, b), identity with `is`"
    )


def _bool_hint(term: Nu) -> str:
    """The TypeError message for ``bool(term)``, naming what the term offers."""
    name = type(term).__name__
    logic = (
        ".and_(), .or_(), .not_()"
        if callable(getattr(type(term), "and_", None))
        else "nu.And, nu.Or, nu.Not"
    )
    return (
        f"a Nu term has no truth value while building a program ({name}): "
        f"use nu.If / nu.IfDo, {logic}. "
        f"Test the term itself with `is None`; walk it with nu.tree"
    )


def _contains_hint(term: Nu) -> str:
    """The TypeError message for ``x in term``, naming what the term offers."""
    name = type(term).__name__
    spelling = (
        "t.contains(x)" if callable(getattr(type(term), "contains", None)) else "nu.Contains(t, x)"
    )
    return f"`x in t` can't build a term ({name}): use {spelling}"


def _iter_hint(term: Nu) -> str:
    """The TypeError message for ``for x in term`` / ``next(term)``."""
    name = type(term).__name__
    return (
        f"a Nu term can't be looped over while building a program ({name}). "
        f"To loop in the program: nu.ForEachDo / nu.Map / nu.Filter, t.iter() "
        f"for a stream, it.next() to pull one item. To walk the term itself: "
        f"nu.tree.preorder(t) / nu.tree.children(t)"
    )


def _len_hint(term: Nu) -> str:
    """The TypeError message for ``len(term)``, naming what the term offers."""
    name = type(term).__name__
    spelling = "t.len()" if callable(getattr(type(term), "len", None)) else "nu.Len(t)"
    return (
        f"len(t) can't build a term ({name}): use {spelling}. "
        f"For the tree's node count use nu.tree.size(t)"
    )
