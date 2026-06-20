"""Minimal Nu-kind shapes for law tests.

Canonical green-path Lego pieces shared across every dimension test in
``tests/nu2/lang/laws/``. Each class is the smallest concrete subclass of a
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

from nu2.engine.structure import Declared
from nu2.lang import (
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
    """A Ref with a default name. Pass ``name=`` to override."""

    def __init__(self, name: str = "x") -> None:
        super().__init__(name)
