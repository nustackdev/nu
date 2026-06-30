"""Minimal Nu-kind shapes for law tests.

Canonical green-path Lego pieces shared across every dimension test in
``tests/nu/lang/laws/``. Each class is the smallest concrete subclass of a
Nu sort that carries the attributes laws read - no ``eval`` / ``compile``,
no payload, no semantics. Tests compose them and assert on the laws that
fire.

Dimension-specific shapes (a Query that wrongly declares WRITE; a Span that
lies about its body's cardinality; an async-only atom) are by definition
malformed and belong inline in the test file that uses them - hoist into
this module only when a second dimension reaches for the same shape.

Naming is intentionally short (``Q``, ``Cmd``, ``Act``, ``Brk``, ...) so
deeply nested compositions in test bodies stay readable, e.g.
``assert_fails(Q(Cmd(R())), "composition")``.
"""

from __future__ import annotations

from nu.engine.structure import Declared
from nu.lang import (
    Bracket,
    Command,
    Control,
    Policy,
    Reduction,
    Ref,
    ScalarAction,
    ScalarQuery,
    Strategy,
    StreamAction,
    StreamQuery,
)


__all__ = [
    "R2",
    "Act",
    "Brk",
    "Cmd",
    "FlowC",
    "FlowS",
    "Pol",
    "Q",
    "R",
    "Red",
    "Stream",
    "StreamAct",
]


class Q(ScalarQuery):
    """A bare ScalarQuery. Yields, declares no effects."""


class Stream(StreamQuery):
    """A bare StreamQuery. Yields a stream, declares no effects."""


class Red(Reduction):
    """A bare Reduction. Folds a stream child to a scalar."""


class Cmd(Command):
    """A bare Command. Slot 0 is the Ref it writes."""

    mutates = Declared(value=frozenset({0}))


class Act(ScalarAction):
    """A bare ScalarAction. Slot 0 is the Ref it writes; yields a value."""

    mutates = Declared(value=frozenset({0}))


class StreamAct(StreamAction):
    """A bare StreamAction. Slot 0 is the Ref it writes; yields a stream."""

    mutates = Declared(value=frozenset({0}))


class FlowS(Strategy):
    """A bare Strategy. Holds mutator children directly."""


class FlowC(Control):
    """A bare Control. Holds mutator children under Query-typed parameters."""


class Brk(Bracket):
    """A bare Bracket. Wraps one body."""


class Pol(Policy):
    """A bare Policy. Wraps one body."""


class R(Ref):
    """A concrete test Ref - one fabric.

    Like every concrete Ref, it owns its name (in payload); the base ``Ref``
    carries none. The effect system keys off the Ref's *class*, not the name,
    so the name is a free label here - two ``R`` instances share one fabric.
    For a second, distinct fabric in a test, use :class:`R2`.
    """

    def __init__(self, name: str = "x") -> None:
        super().__init__()
        self.payload = {"name": name}


class R2(Ref):
    """A second concrete test Ref - a distinct fabric from :class:`R`.

    Same shape as ``R`` but a different class, so ``(R2, effect)`` tuples are
    independent of ``(R, effect)`` ones. Use it where a test needs two fabrics.
    """

    def __init__(self, name: str = "y") -> None:
        super().__init__()
        self.payload = {"name": name}
