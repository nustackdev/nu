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
``cardinality`` / effect / algebra attributes, so a plain ``Nu(...)`` cannot
pass schema resolution. The algebraic identity element of the tree is
``Span`` (and its sub-shapes ``Bracket`` / ``Policy``), which carries the
TRANSPARENT cardinality and the rest of the forwarding machinery.

``Nu`` is generic over ``V_co``, the yield type, covariant since ``V``
appears only in output positions. The ``R`` parameter of ``Term`` is fixed
to ``Runtime`` at this layer.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from nu2.engine import Term
from nu2.lang.runtime import Runtime


__all__ = ["Nu"]


V_co = TypeVar("V_co", covariant=True)


class Nu(Term[Runtime, V_co], Generic[V_co]):  # noqa: UP046  # PEP 695 has no variance markers
    """The user-facing base for every Nu construct.

    A tagged ``Term`` carrying the language's ``Runtime`` binding and a
    yield type ``V_co``. Abstract -- concrete sorts declare the structural,
    effect, cardinality, async, and algebra attributes the engine requires.
    """

    def __init__(self, *children: object) -> None:
        # Auto-wrap any non-Term child as Literal so `Add(1, 2)` reads the
        # same as `Add(Literal(1), Literal(2))`. Lazy import keeps the lang
        # layer free of a core dependency.
        from nu2.core import LiteralQuery

        wrapped = tuple(c if isinstance(c, Term) else LiteralQuery(c) for c in children)
        super().__init__(*wrapped)

    # --- composition operators ------------------------------------------
    #
    # Sugar for the Strategy flows: ``a >> b`` is ``Sequential(a, b)``,
    # ``a | b`` is ``Parallel(a, b)``, ``a & b`` is ``Race(a, b)``. Lazy
    # imports keep the lang base free of a flows dependency (flows import
    # from lang). Each call builds a fresh two-child Strategy; chains nest
    # left-to-right (``a >> b >> c`` is ``Sequential(Sequential(a, b), c)``),
    # which the associativity attribute lets the engine flatten.

    def __rshift__(self, other: object) -> Nu:
        from nu2.flows import Sequential

        return Sequential(self, other)

    def __or__(self, other: object) -> Nu:
        from nu2.flows import Parallel

        return Parallel(self, other)

    def __and__(self, other: object) -> Nu:
        from nu2.flows import Race

        return Race(self, other)
