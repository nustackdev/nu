"""The Nu kind taxonomy: the user-facing Term classes that declare each sort.

A taxonomy of ``Nu`` subclasses. The leaves (``Ref``, ``ScalarQuery``,
``StreamQuery``, ``Reduction``, ``Command``, ``Strategy``, ``Control``,
``Bracket``, ``Policy``) carry the sort and cardinality bindings concrete
nodes use. The interiors (``Interaction``, ``Query``, ``Flow``, ``Span``) are
abstract groupings for ``subsort`` queries and for the dispatch surface
``Interaction.eval`` / ``aeval``.

"Kind" is the Python class of a Term (Ref, Interaction, ...); "sort" is the
attribute concern naming the structural category. This module sits on top
of ``nu2.lang.nu`` (the base) and ``nu2.lang.attributes`` (Sort and
Cardinality value spaces).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine import Declared, Term

from .attributes import Cardinality, Sort
from .nu import Nu


if TYPE_CHECKING:
    from nu2.lang.runtime import Runtime

__all__ = [
    "Bracket",
    "Command",
    "Control",
    "Flow",
    "Interaction",
    "Policy",
    "Query",
    "Reduction",
    "Ref",
    "ScalarQuery",
    "Span",
    "Strategy",
    "StreamQuery",
]


class Ref(Nu):
    """A name for a Context location: a leaf, or keyed by child Refs."""

    sort = Declared(value=Sort.REF)
    cardinality = Declared(value=Cardinality.SCALAR)

    def __init__(self, name: str, *key: Term) -> None:
        super().__init__(*key)
        self.payload = {"name": name}


class Interaction(Nu):
    """Abstract: a node that interacts with the Context. Never instantiated.

    Concrete sub-kinds implement ``eval`` / ``aeval`` to drive execution.
    Both receive the per-execution ``Runtime`` and the node's ``nid`` (its
    integer position in the attributed program); they recurse via
    ``rt.eval(child_nid)`` and reach for ``self.children`` / ``self.payload``
    directly. Attribute reads use ``rt.program.attrs[name][nid]``.
    """

    def eval(self, rt: Runtime, nid: int) -> object:
        """Evaluate this node synchronously; return its value or None."""
        msg = f"{type(self).__name__}.eval is not implemented"
        raise NotImplementedError(msg)

    async def aeval(self, rt: Runtime, nid: int) -> object:
        """Evaluate this node asynchronously; return its value or None."""
        msg = f"{type(self).__name__}.aeval is not implemented"
        raise NotImplementedError(msg)


class Query(Interaction):
    """Abstract: a value-producing Interaction."""


class ScalarQuery(Query):
    """A Query that yields exactly one value."""

    sort = Declared(value=Sort.SCALAR_QUERY)
    cardinality = Declared(value=Cardinality.SCALAR)


class StreamQuery(Query):
    """A Query that yields zero or more values."""

    sort = Declared(value=Sort.STREAM_QUERY)
    cardinality = Declared(value=Cardinality.STREAM)


class Reduction(ScalarQuery):
    """A ScalarQuery that folds a stream child down to one value."""

    sort = Declared(value=Sort.REDUCTION)


class Command(Interaction):
    """A mutating Interaction. Yields nothing; its only sub-shape is scalar."""

    sort = Declared(value=Sort.SCALAR_COMMAND)
    cardinality = Declared(value=Cardinality.VOID)


class Flow(Interaction):
    """Abstract: a Command-composing Interaction. Yields nothing."""

    cardinality = Declared(value=Cardinality.VOID)


class Strategy(Flow):
    """A Flow that composes Commands directly."""

    sort = Declared(value=Sort.STRATEGY)


class Control(Flow):
    """A Flow that composes Commands under Query parameters."""

    sort = Declared(value=Sort.CONTROL)


class Span(Interaction):
    """Abstract: a transparent Interaction; yields what its body yields."""

    cardinality = Declared(value=Cardinality.TRANSPARENT)


class Bracket(Span):
    """A Span that governs a body's lifecycle."""

    sort = Declared(value=Sort.BRACKET)


class Policy(Span):
    """A Span that governs a body's execution on failure."""

    sort = Declared(value=Sort.POLICY)
