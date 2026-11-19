"""The Nu kind taxonomy: the user-facing Term classes that declare each sort.

A taxonomy of ``Nu`` subclasses. The leaves (``Ref``, ``ScalarQuery``,
``StreamQuery``, ``Command``, ``ScalarAction``, ``StreamAction``,
``Strategy``, ``Control``, ``Bracket``, ``Policy``) carry the sort and
cardinality bindings concrete nodes use. The interiors (``Interaction``,
``Query``, ``Action``, ``Flow``, ``Span``) are abstract groupings for
``subsort`` queries and for the dispatch surface ``Interaction._eval`` /
``_aeval``.

A reduction is not a kind. A kind says whether a node mutates and what it
gives out; a reduction says what one of its slots takes in: a stream, folded
to whatever the kind gives out. So ``Reduction`` is a mixin that declares
``reduces``, the index of that slot, and each scalar-out kind has its own
reduction base: ``QueryReduction`` reads and yields one value,
``ActionReduction`` writes and yields one value, ``CommandReduction`` writes
and yields nothing. Each keeps its kind's sort, cardinality and composition
rules; the cardinality laws read ``reduces`` to let the stream into that
one slot.

"Kind" is the Python class of a Term (Ref, Interaction, ...); "sort" is the
attribute concern naming the structural category. This module sits on top
of ``nu.lang.nu`` (the base) and ``nu.lang.attributes`` (Sort and
Cardinality value spaces).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.engine import Declared

from .attributes import Cardinality, Sort
from .nu import Nu


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime

V_co = TypeVar("V_co", covariant=True)

__all__ = [
    "Action",
    "ActionReduction",
    "Bracket",
    "Command",
    "CommandReduction",
    "Control",
    "Flow",
    "Interaction",
    "Policy",
    "Query",
    "QueryReduction",
    "Reduction",
    "Ref",
    "ScalarAction",
    "ScalarQuery",
    "Span",
    "Strategy",
    "StreamAction",
    "StreamQuery",
]


class Ref(Nu[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A name for a location in a Fabric: the abstract Ref kind.

    A Ref is the only atom that touches Context, but it touches it through a
    Fabric, and each Fabric has its own concrete Ref (``Attr`` for the
    Context-attrs fabric, fabric / shape Refs for others). This base is bare:
    it declares only the sort and cardinality every Ref shares and nothing
    else - no name, no read, no write. A bare ``Ref`` is for structural
    analysis; to run, use a concrete fabric Ref.

    A Ref names a location, but the location is never knowable from the base:
    it can be static or computed, and it lives in the concrete fabric Ref, not
    here. What the effect system reads off a Ref is its *fabric*, identified by
    its concrete class, never a location name (which may not exist statically).
    """

    _sort = Declared(value=Sort.REF, name="sort")
    _cardinality = Declared(value=Cardinality.SCALAR, name="cardinality")


class Interaction(Nu[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a node that interacts with the Context. Never instantiated.

    Concrete sub-kinds implement ``_eval`` / ``_aeval`` to drive execution.
    Both receive the per-execution ``Runtime`` and the node's ``nid`` (its
    integer position in the attributed program); they recurse via
    ``rt.eval(child_nid)`` and reach for ``self._children`` and their own fields
    directly. Attribute reads use ``rt.program.attrs[name][nid]``.
    """

    def _eval(self, rt: Runtime, nid: int) -> V_co:
        """Evaluate this node synchronously; return its value or None."""
        msg = f"{type(self).__name__}._eval is not implemented"
        raise NotImplementedError(msg)

    async def _aeval(self, rt: Runtime, nid: int) -> V_co:
        """Evaluate this node asynchronously; return its value or None."""
        msg = f"{type(self).__name__}._aeval is not implemented"
        raise NotImplementedError(msg)


class Query(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a value-producing Interaction."""


class ScalarQuery(Query[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Query that yields exactly one value."""

    _sort = Declared(value=Sort.SCALAR_QUERY, name="sort")
    _cardinality = Declared(value=Cardinality.SCALAR, name="cardinality")


class StreamQuery(Query[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Query that yields zero or more values."""

    _sort = Declared(value=Sort.STREAM_QUERY, name="sort")
    _cardinality = Declared(value=Cardinality.STREAM, name="cardinality")


class Command(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A mutating Interaction. Yields nothing; its only sub-shape is scalar."""

    _sort = Declared(value=Sort.SCALAR_COMMAND, name="sort")
    _cardinality = Declared(value=Cardinality.VOID, name="cardinality")


class Action(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a dual-citizen Interaction. Mutates Context and yields a value."""


class ScalarAction(Action[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """An Action that mutates and yields exactly one value."""

    _sort = Declared(value=Sort.SCALAR_ACTION, name="sort")
    _cardinality = Declared(value=Cardinality.SCALAR, name="cardinality")


class StreamAction(Action[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """An Action that mutates and yields zero or more values.

    The stream-shaped twin of ScalarAction: one atomic mutate-and-yield-many
    (drain a queue, ``DELETE ... RETURNING`` over a predicate). A scalar
    consumer must reduce it like any StreamQuery; the cardinality law gates
    that off ``cardinality`` alone, with no per-kind special case.
    """

    _sort = Declared(value=Sort.STREAM_ACTION, name="sort")
    _cardinality = Declared(value=Cardinality.STREAM, name="cardinality")


class Flow(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a Command-composing Interaction. Yields nothing."""

    _cardinality = Declared(value=Cardinality.VOID, name="cardinality")


class Strategy(Flow[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Flow that composes Commands directly."""

    _sort = Declared(value=Sort.STRATEGY, name="sort")


class Control(Flow[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Flow that composes Commands under Query parameters."""

    _sort = Declared(value=Sort.CONTROL, name="sort")


class Span(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a transparent Interaction; yields what its body yields."""

    _cardinality = Declared(value=Cardinality.TRANSPARENT, name="cardinality")


class Bracket(Span[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Span that governs a body's lifecycle."""

    _sort = Declared(value=Sort.BRACKET, name="sort")


class Policy(Span[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Span that governs a body's execution on failure."""

    _sort = Declared(value=Sort.POLICY, name="sort")


# --- reductions: a slot role, not a kind -------------------------------------


class Reduction(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: an Interaction with one slot that takes a stream and folds it.

    Declares ``reduces``, the index of that slot, 0 by default; a subclass
    moves it by redeclaring ``_reduces``. Carries no sort or cardinality of
    its own: mix it with a scalar-out kind, through ``QueryReduction``,
    ``ActionReduction`` or ``CommandReduction``. Every other slot of the node
    stays scalar.
    """

    _reduces = Declared(value=0, name="reduces")


class QueryReduction(Reduction[V_co], ScalarQuery[V_co]):
    """A ScalarQuery that folds a stream down to one value (``Sum``, ``Collect``)."""


class ActionReduction(Reduction[V_co], ScalarAction[V_co]):
    """A ScalarAction that folds a stream into one write and yields one value.

    A blob store fed a stream of pieces that yields the new id.
    """


class CommandReduction(Reduction[V_co], Command[V_co]):
    """A Command that folds a stream into one write and yields nothing.

    Appending a whole stream to a log in one write.
    """
