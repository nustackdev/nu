"""Cardinality laws: which slots may take a stream.

A node that gives out one value or nothing (a ScalarQuery, a ScalarAction, a
Command, a Ref, a Dyn) has scalar slots: a stream child there is refused,
because nothing says how to fold it. A reduction is the exception, and only
in one slot: it declares ``reduces``, the index of the slot whose stream it
folds, and that slot must hold a stream. The refusal reads slots, not kinds,
so a read, a write that yields and a write that yields nothing can each fold
a stream the same way.

Flows and Spans are out of scope: a Flow's slots are parameters and bodies
its own laws govern, and a Span yields what its body yields. A StreamQuery
or StreamAction consumer (``Map``, ``Filter``) takes streams in any slot.

A stream is lazy: it runs only as far as something pulls it. ``stream_is_pulled``
warns on a stream nothing pulls. Looking through Spans to the slot the stream
sits in, it is pulled at the program root (the caller pulls), under a node that
yields a stream, in a reduction's ``reduces`` slot, or in a param or config
slot (``ForEachDo`` walks its source). A scalar or command parent is left to
``scalar_stream_refused`` and a stream query in a body slot to
``flow_body_is_mutator``; what remains is a stream action in a Flow body slot,
which validates and does nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu.engine import Law, Severity, predicate
from nu.lang.attributes import Attr, Cardinality, Sort, subsort

from .composition import _MUTATING_SORTS, _effective_sort
from .predicates import cardinality_is, child_paths, of_sort


if TYPE_CHECKING:
    from nu.engine import Path, Program
    from nu.lang.nu import Nu


__all__ = ["LAWS"]


def _stream_slots(program: Program, path: Path) -> list[int]:
    """The slot indices whose child resolves to a stream."""
    return [
        slot
        for slot, child in enumerate(child_paths(program, path))
        if program.attr(child, Attr.CHILD_CARDINALITY) is Cardinality.STREAM
    ]


def _stray_stream_slots(program: Program, path: Path) -> list[int]:
    """The stream slots other than the node's declared reduction slot."""
    reduces = program.attr(path, Attr.REDUCES)
    return [slot for slot in _stream_slots(program, path) if slot != reduces]


def _kind(program: Program, path: Path) -> str:
    return type(program.terms[program.id_of[path]]).__name__


@predicate
def streams_only_in_reduction_slot(program: Program, path: Path) -> bool:
    """Holds when every stream child sits in the node's ``reduces`` slot."""
    return not _stray_stream_slots(program, path)


def _stream_refused_message(program: Program, path: Path) -> str:
    slots = ", ".join(str(s) for s in _stray_stream_slots(program, path))
    reduces = program.attr(path, Attr.REDUCES)
    if reduces is None:
        why = "it is no reduction, so every slot takes one value"
    else:
        why = f"only its reduction slot {reduces} takes a stream"
    return (
        f"{_kind(program, path)} is fed a stream in slot {slots}: {why}; "
        "fold the stream first (nu.Collect, nu.First, ...) or use a reduction"
    )


@predicate
def is_reduction(program: Program, path: Path) -> bool:
    """Nodes that declare a reduction slot."""
    return program.attr(path, Attr.REDUCES) is not None


@predicate
def reduction_slot_yields_stream(program: Program, path: Path) -> bool:
    """Holds when the child in the node's ``reduces`` slot resolves to a stream."""
    return program.attr(path, Attr.REDUCES) in _stream_slots(program, path)


def _reduction_message(program: Program, path: Path) -> str:
    reduces = program.attr(path, Attr.REDUCES)
    children = child_paths(program, path)
    if reduces >= len(children):
        got = f"it has {len(children)} slot(s)"
    else:
        got = f"it holds a {program.attr(children[reduces], Attr.CHILD_CARDINALITY)} child"
    return f"{_kind(program, path)} folds the stream in slot {reduces}, but {got}"


def _yields_stream(program: Program, path: Path) -> bool:
    return program.attr(path, Attr.CHILD_CARDINALITY) is Cardinality.STREAM


@predicate
def yields_stream(program: Program, path: Path) -> bool:
    """Nodes whose resolved cardinality is a stream."""
    return _yields_stream(program, path)


@predicate
def stream_has_puller(program: Program, path: Path) -> bool:
    """Holds when something pulls the stream at ``path``, or another law owns it.

    A Span parent forwards the stream: the Span is a stream itself and is
    judged in its place, so the body holds here and the stream is reported
    once, at the node sitting directly in the slot that does not pull.
    """
    if not path:
        return True
    parent, slot = path[:-1], path[-1]
    sort: Sort = program.attr(parent, Attr.SORT)
    if subsort(sort, Sort.SPAN) or _yields_stream(program, parent):
        return True
    if program.attr(parent, Attr.CARDINALITY) is Cardinality.SCALAR or subsort(sort, Sort.COMMAND):
        return True
    if slot == program.attr(parent, Attr.REDUCES):
        return True
    params: frozenset[int] = program.attr(parent, Attr.PARAM_SLOTS)
    config = cast("Nu", program.terms[program.id_of[parent]])._config_slots()
    if slot in params or slot in config:
        return True
    # A body slot takes mutators only: a stream query there is already refused.
    sort = _effective_sort(program, path)
    return not any(subsort(sort, m) for m in _MUTATING_SORTS)


def _unpulled_message(program: Program, path: Path) -> str:
    return (
        f"{_kind(program, path)} yields a stream nothing pulls: streams are lazy and do "
        "nothing until consumed; pull it with a reduction (nu.Collect, .to_list()) "
        "or ForEachDo, or use a command"
    )


LAWS: tuple[Law, ...] = (
    Law(
        "scalar_stream_refused",
        scope=cardinality_is(Cardinality.SCALAR) | of_sort(Sort.COMMAND),
        holds=streams_only_in_reduction_slot,
        message=_stream_refused_message,
    ),
    Law(
        "reduction_takes_stream",
        scope=is_reduction,
        holds=reduction_slot_yields_stream,
        message=_reduction_message,
    ),
    Law(
        "stream_is_pulled",
        scope=yields_stream,
        holds=stream_has_puller,
        message=_unpulled_message,
        severity=Severity.WARNING,
    ),
)
