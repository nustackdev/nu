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
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Law, predicate
from nu.lang.attributes import Attr, Cardinality, Sort

from .predicates import cardinality_is, child_paths, of_sort


if TYPE_CHECKING:
    from nu.engine import Path, Program


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
)
