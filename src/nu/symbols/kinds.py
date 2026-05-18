"""Nu's Symbol kinds: the atom classes built on the engine.

Each kind is a thin bag of declared attributes on top of ``engine.Symbol``.
The abstract bases (Query, Command, Flow, Span and their sub-kinds) carry the
shared declarations; the concrete atoms below them carry only their own.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Attribute, Symbol
from nu.symbols.sorts import Effect, Mode


if TYPE_CHECKING:
    from typing import Any

__all__ = [
    "Add",
    "Append",
    "AsyncFetch",
    "BlockingScan",
    "Bracket",
    "Collect",
    "Command",
    "Control",
    "Copy",
    "Delete",
    "Eq",
    "Filter",
    "First",
    "Flow",
    "ForEachDo",
    "Gather",
    "IfDo",
    "ItemsOf",
    "Last",
    "Literal",
    "Map",
    "Mul",
    "Not",
    "Parallel",
    "Policy",
    "Query",
    "Race",
    "Range",
    "Reduction",
    "Ref",
    "Retry",
    "ScalarQuery",
    "Sequential",
    "Snapshot",
    "Span",
    "Store",
    "Strategy",
    "StreamQuery",
    "Sum",
    "Take",
    "Transaction",
    "TryCatch",
    "WhileDo",
]


# --- Ref -----------------------------------------------------------------


class Ref(Symbol):
    """A name for a location. A leaf, or a dynamic Ref with key children."""

    sort = Attribute.declared("Ref")
    realization = Attribute.declared("scalar")

    def __init__(self, name: str, *key: Symbol) -> None:
        super().__init__(*key)
        self.payload = {"name": name}


# --- Query ---------------------------------------------------------------


class Query(Symbol):
    """Abstract: a value-producing Interaction. Not instantiated directly."""


class ScalarQuery(Query):
    """Abstract: a Query that yields exactly one value."""

    sort = Attribute.declared("ScalarQuery")
    realization = Attribute.declared("scalar")


class StreamQuery(Query):
    """Abstract: a Query that yields zero or more values."""

    sort = Attribute.declared("StreamQuery")
    realization = Attribute.declared("stream")


class Reduction(ScalarQuery):
    """Abstract: a ScalarQuery that folds a stream child to one value."""

    sort = Attribute.declared("Reduction")
    is_reduction = Attribute.declared(True)


class Literal(ScalarQuery):
    """An irreducible leaf holding a value, yielded once. Pure."""

    def __init__(self, value: Any) -> None:  # noqa: ANN401
        super().__init__()
        self.payload = {"value": value}


class Add(ScalarQuery):
    """Add two scalar queries."""


class Mul(ScalarQuery):
    """Multiply two scalar queries."""


class Eq(ScalarQuery):
    """Test two scalar queries for equality."""


class Not(ScalarQuery):
    """Negate a scalar query."""


class AsyncFetch(ScalarQuery):
    """Fetch a value over an async-only fabric."""

    support = Attribute.declared(frozenset({Mode.ASYNC}))


class BlockingScan(ScalarQuery):
    """Scan a value over a sync-only (blocking) fabric."""

    support = Attribute.declared(frozenset({Mode.SYNC}))


class Collect(Reduction):
    """Drain a stream child into a list."""


class First(Reduction):
    """Take the first value of a stream child."""


class Last(Reduction):
    """Take the last value of a stream child."""


class Sum(Reduction):
    """Sum a stream child."""


class Range(StreamQuery):
    """Yield the integers below a scalar bound."""


class ItemsOf(StreamQuery):
    """Yield each item held at a collection Ref."""


class Map(StreamQuery):
    """Yield each value of a source stream through a transform."""


class Filter(StreamQuery):
    """Yield each value of a source stream that satisfies a predicate."""


class Take(StreamQuery):
    """Yield at most a scalar count of a source stream's values."""


# --- Command -------------------------------------------------------------


class Command(Symbol):
    """Abstract: a mutating Interaction. Yields nothing."""

    sort = Attribute.declared("ScalarCommand")
    realization = Attribute.declared("none")


class Store(Command):
    """Write a value to a target Ref."""

    own_effects = Attribute.declared({0: Effect.WRITE})


class Copy(Command):
    """Copy the value at a source Ref to a target Ref."""

    own_effects = Attribute.declared({1: Effect.WRITE})


class Append(Command):
    """Append a value to a collection Ref."""

    own_effects = Attribute.declared({0: Effect.WRITE})


class Delete(Command):
    """Remove the location named by a Ref."""

    own_effects = Attribute.declared({0: Effect.WRITE})


# --- Flow ----------------------------------------------------------------


class Flow(Symbol):
    """Abstract: a Command-composing Interaction. Yields nothing."""

    realization = Attribute.declared("none")


class Strategy(Flow):
    """Abstract: a Flow that composes Commands directly."""

    sort = Attribute.declared("Strategy")


class Control(Flow):
    """Abstract: a Flow that composes Commands under Query parameters."""

    sort = Attribute.declared("Control")


class Sequential(Strategy):
    """Run child Commands in order."""


class Parallel(Strategy):
    """Run child Commands concurrently."""

    concurrent = Attribute.declared(True)


class Race(Strategy):
    """Run child Commands concurrently; the first to finish wins."""

    concurrent = Attribute.declared(True)


class Gather(Strategy):
    """Run child Commands concurrently; join on all of them."""

    concurrent = Attribute.declared(True)


class IfDo(Control):
    """Run a body Command when a condition Query holds."""


class ForEachDo(Control):
    """Run a body Command for each value of an items Query."""


class WhileDo(Control):
    """Run a body Command while a condition Query holds."""


# --- Span ----------------------------------------------------------------


class Span(Symbol):
    """Abstract: a transparent Interaction; forwards its body's yield."""

    realization = Attribute.declared("body")


class Bracket(Span):
    """Abstract: a Span that governs a body's lifecycle."""

    sort = Attribute.declared("Bracket")


class Policy(Span):
    """Abstract: a Span that governs a body's execution on failure."""

    sort = Attribute.declared("Policy")


class Snapshot(Bracket):
    """Run a body against a snapshot of the Context."""


class Transaction(Bracket):
    """Run a body transactionally."""


class Retry(Policy):
    """Re-run a body on failure, up to an attempts Query."""


class TryCatch(Policy):
    """Run a body; on failure, run a fallback body."""
