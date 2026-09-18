"""Nu - the user-facing base class for every Nu construct.

A thin subclass of ``Term``. Every concrete Nu sort (``Ref``, ``Interaction``,
``ScalarQuery``, ``StreamQuery``, ...) descends from ``Nu``; users annotate
their applications with ``Nu`` rather than reaching for the engine-level
``Term``. Engine machinery still operates on ``Term`` and accepts any ``Nu``
transparently - this class adds no behavior, only a brand surface.

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

from typing import Generic, TypeVar, cast

from nu.engine import Term
from nu.lang.runtime import Runtime


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

    def __rshift__(self, other: object) -> Nu:
        from nu.core.flows import Sequential

        return Sequential(self, other)

    def __or__(self, other: object) -> Nu:
        from nu.core.flows import Parallel

        return Parallel(self, other)

    def __and__(self, other: object) -> Nu:
        from nu.core.flows import Race

        return Race(self, other)
