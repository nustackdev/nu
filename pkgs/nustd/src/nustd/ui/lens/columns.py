"""What a Shape is worth as columns, read wherever the Shape actually lives.

Two things say where to read and what to expect there, and they are separate on
purpose:

- **shape** is a Shape class. It says what structure to expect, and it is the
  root the browser's cursor is relative to. Segment one of a cursor names a slot
  on it.
- **prefix** is a Ref. It says where that structure sits, and it carries which
  store, because a Ref chain resolves its Navigator by the class it is rooted
  at and a bare path tuple would lose that. Leave it out and the shape is read
  at the root of its own store, which is how every kv program addresses today.

The read is prefix, then cursor: each slot ref is built with the level above it
as its parent, so the cursor only ever appends. **The prefix never crosses the
wire.** The browser sends a cursor relative to ``shape`` and gets columns back;
it is never told where any of it lives, and it cannot walk above the prefix
because there is no string path to walk up -- a segment that names no slot
yields an error column and nothing else.

The one hard trick is that the address arrives at runtime:

- :func:`column_terms` is an **ordinary ``-> Nu`` builder**. Given a Shape
  class, a concrete cursor and a prefix it walks the Shape in python and
  returns a Nu term that reads whatever kv has to be read. A function, not an
  atom: it composes, and it introduces no thunk.
- :data:`LensColumns` is that builder behind :func:`nu.host`, so the cursor can
  be a runtime value. The callable is fixed at class definition time, which is
  the sanctioned escape -- the callable is code, not data. Its children are the
  shape and the prefix (both addresses), the cursor and the cap.
- :func:`columns` hands ``LensColumns`` to :class:`nu.Eval`, which compiles the
  produced term against the running program and drives it in the same ctx.

Dispatch is on the kernel Ref families, never on anything a storage layer
declares: ``DictRef`` is a ``MappingRef``, ``StrRef`` is an ``ItemRef``, and
that is the whole protocol. So a slot declared ``DictRef(object)`` opens as a
mapping and shows exactly what a program wrote into it, keys no Shape ever
named included -- the shape supplies the protocol, kv supplies the contents.
The walk stops only at something no shape declares as a container at all.

Nothing here opens a store, and nothing here imports a fabric. Building the
term needs no Navigator; only running it touches one. So the storage boundary
belongs to whoever runs the term: :func:`nustd.ui.lens.browse` places it for
you, and a caller wiring the arm by hand writes the ``nustd.kv.Snapshot(...)``
itself. An ``Eval`` is opaque to the static effect walk, so that bracket can
never be inferred from the tree.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import nu
from nu.domains.shape import (
    ItemRef,
    MappingRef,
    SequenceRef,
    ShapeRef,
    ShapesMappingRef,
    ShapesSequenceRef,
)
from nu.lang import EMPTY, INVALID, Cardinality


if TYPE_CHECKING:
    from nu.domains.shape import Shape
    from nu.domains.shape.refs import StructuredRef


__all__ = [
    "DEFAULT_MAX_ROWS",
    "LensCell",
    "LensColumns",
    "LensFailed",
    "column_terms",
    "columns",
]


#: How many rows one column ships. Hard cap, no pagination: the browser seeds
#: from the same number in its mount props, and a column says ``n/total`` when
#: it has been clipped. The cap clips what is shipped, not what is read.
DEFAULT_MAX_ROWS = 200

#: What a row's ``preview`` is trimmed to, and what the leaf reader pane gets.
PREVIEW = 120
TEXT = 4000


def _loop(depth: int) -> tuple[str, nu.Nu]:
    """The name one column's ``Map`` binds its element under, and a ref for it.

    Per column rather than one shared name: columns are siblings under one
    ``List``, and two of them binding one key would read each other's element
    the moment either awaited.
    """
    name = f"_lens_item{depth}"
    return name, nu.AnyAttrRef(name)


# --- one row ----------------------------------------------------------------


def _vtype(value: object) -> str:
    """The wire word for a value's type. Sentinels get their own words."""
    if value is EMPTY:
        return "empty"
    if value is INVALID:
        return "invalid"
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float, str, bytes, list, tuple, dict)):
        return {"tuple": "list"}.get(type(value).__name__, type(value).__name__)
    return type(value).__name__


def _text(value: object) -> str:
    """A value as the browser should read it. Strings unquoted, the rest repr'd."""
    if value is EMPTY or value is INVALID or value is None:
        return ""
    return value if isinstance(value, str) else repr(value)


def _cell(key: str, value: object, kind: str, navigable: bool, full: bool) -> dict[str, Any]:
    """One wire row, plus the untruncated ``text`` when ``full``.

    A row is ``{key, kind, preview, navigable, vtype}``. ``full`` is the leaf
    column's single row, which gets a reader pane; every other row is a line in
    a list and carries the trimmed preview only.
    """
    body = _text(value)
    row: dict[str, Any] = {
        "key": key,
        "kind": kind,
        "preview": body[:PREVIEW],
        "navigable": navigable,
        "vtype": _vtype(value),
    }
    if full:
        row["text"] = body[:TEXT]
        row["clipped"] = len(body) > TEXT
    return row


#: One row, from one value. Sentinels are the answer here rather than a reason
#: to short-circuit: an unwritten slot renders as ``empty``, visibly.
LensCell = nu.host(_cell, name="LensCell", propagate_sentinels=False)


def _door(key: nu.Nu, kind: str) -> nu.Nu:
    """A row that is a way in rather than a value.

    A Shape under a key, or at a position. It says which kind of column it
    opens and touches the store for nothing.
    """
    return nu.Dict.of(
        key=key,
        kind=nu.Str(kind),
        preview=nu.Str(""),
        navigable=nu.Bool(True),
        vtype=nu.Str(""),
    )


# --- the walk ---------------------------------------------------------------


def _kind_of(ref_cls: type) -> str:
    """The column a ref of this class opens. The browser's ``kind`` vocabulary."""
    if issubclass(ref_cls, (ShapesMappingRef, MappingRef)):
        return "mapping"
    if issubclass(ref_cls, (ShapesSequenceRef, SequenceRef)):
        return "sequence"
    if issubclass(ref_cls, ShapeRef):
        return "shape"
    if issubclass(ref_cls, ItemRef):
        return "leaf"
    return "unknown"


def _slot(shape_cls: type[Shape], name: str, parent: StructuredRef | None) -> Any:  # noqa: ANN401
    """One named slot of ``shape_cls``, built under ``parent``.

    The one place a level is made, so the prefix reaches the deepest read the
    same way a nested slot does: as somebody's parent. There is no path tuple
    anywhere to concatenate, which is what makes a cursor unable to name
    anything above the prefix.
    """
    slot = shape_cls._slots.get(name)
    if slot is None:
        msg = f"{name!r}: no such slot on {shape_cls.__name__}"
        raise KeyError(msg)
    return slot.create_ref(owner_shape=shape_cls, parent_ref=parent)


def _descend(prefix: StructuredRef | None, shape_cls: type[Shape], cursor: tuple[str, ...]) -> Any:  # noqa: ANN401
    """The ref at ``cursor``, built segment by segment from ``prefix``.

    The first segment is a slot on ``shape_cls``; after that each level decides
    how it is indexed. Raises on a segment that names nothing, which the caller
    turns into one error column.
    """
    ref = _slot(shape_cls, cursor[0], prefix)
    for seg in cursor[1:]:
        if isinstance(ref, ItemRef):
            # A leaf has nothing under it, and indexing one builds a term that
            # fails much later, inside the codec, with a much worse message.
            msg = f"{seg!r}: a value has nothing under it"
            raise KeyError(msg)
        if isinstance(ref, ShapeRef):
            ref = _slot(ref._payload["shape_type"], seg, ref)
        elif isinstance(ref, (ShapesSequenceRef, SequenceRef)):
            # A position is an int and a wire segment is a string, always.
            ref = ref[int(seg)]
        else:
            ref = ref[seg]
    return ref


def _column(kind: str, entries: nu.Nu, total: nu.Nu) -> nu.Nu:
    """One column, in the shape the browser's slice reads."""
    return nu.Dict.of(kind=nu.Str(kind), entries=entries, total=total)


def _shape_term(shape_cls: type[Shape], at: StructuredRef | None) -> nu.Nu:
    """A Shape's slots, one row each. Leaf slots carry their value.

    The slot list is schema, so it is settled here in python and there is
    nothing to cap; only the leaf slots read anything, and each of those is a
    plain ref read the compiler sees.
    """
    entries: list[nu.Nu] = []
    for name, slot in shape_cls._slots.items():
        kind = _kind_of(slot.ref_cls)
        if kind == "leaf":
            entries.append(LensCell(name, _slot(shape_cls, name, at), kind, True, False))
        else:
            entries.append(
                nu.Literal(
                    {"key": name, "kind": kind, "preview": "", "navigable": True, "vtype": ""}
                )
            )
    return _column("shape", nu.List.of(*entries), nu.Int(len(entries)))


def _mapping_term(ref: StructuredRef, max_rows: int, depth: int) -> nu.Nu:
    """A mapping's keys, capped, with the total beside them.

    Bound once with ``Let``: the cap and the total are two reads of one key
    list, and iterating a container twice to answer one column would be a
    second pass over the store for nothing.
    """
    held = f"_lens_keys{depth}"
    item, elem = _loop(depth)
    keys = nu.ListAttrRef(held)
    if isinstance(ref, ShapesMappingRef):
        row: nu.Nu = _door(nu.ToStr(elem), "shape")
    else:
        row = LensCell(nu.ToStr(elem), ref[elem], nu.Str("leaf"), nu.Bool(True), nu.Bool(False))
    return nu.Let(
        held,
        nu.list(ref.keys()),
        body=_column(
            "mapping",
            nu.Collect(nu.Map(nu.GetItem(keys, nu.Slice(None, max_rows, None)), row, key=item)),
            nu.Len(keys),
        ),
    )


def _sequence_term(ref: StructuredRef, max_rows: int, depth: int) -> nu.Nu:
    """A sequence's elements, capped, keyed by position.

    A sequence of Shapes keys its rows the same way and makes them doors: the
    position is the whole row, and what is behind it is a column of its own.
    """
    held = f"_lens_items{depth}"
    item, elem = _loop(depth)
    items = nu.ListAttrRef(held)
    index = nu.ToStr(nu.GetItem(elem, nu.Int(0)))
    if isinstance(ref, ShapesSequenceRef):
        row: nu.Nu = _door(index, "shape")
    else:
        row = LensCell(
            index,
            nu.GetItem(elem, nu.Int(1)),
            nu.Str("leaf"),
            nu.Bool(False),
            nu.Bool(False),
        )
    return nu.Let(
        held,
        nu.Collect(nu.Iter(ref)),
        body=_column(
            "sequence",
            nu.Collect(
                nu.Map(
                    nu.Enumerate(nu.GetItem(items, nu.Slice(None, max_rows, None))),
                    row,
                    key=item,
                )
            ),
            nu.Len(items),
        ),
    )


def _leaf_term(ref: StructuredRef) -> nu.Nu:
    """One value, in full. The only column with a reader pane."""
    return _column(
        "leaf",
        nu.List.of(LensCell(nu.Str("value"), ref, nu.Str("leaf"), nu.Bool(False), nu.Bool(True))),
        nu.Int(1),
    )


def _failed(what: str) -> dict[str, Any]:
    """One column, for a segment that could not be followed or read.

    Same shape as every other column, so the browser needs no second render
    path for it and the cascade stays a list of columns.
    """
    return {
        "kind": "leaf",
        "entries": [
            {
                "key": "error",
                "kind": "leaf",
                "preview": what[:PREVIEW],
                "navigable": False,
                "vtype": "error",
                "text": what[:TEXT],
                "clipped": len(what) > TEXT,
            }
        ],
        "total": 1,
    }


#: :func:`_failed` as an atom, for the failure only a run can find. A column
#: built at construction is a ``Literal``; this one is built from a caught
#: error, so it needs a term.
LensFailed = nu.host(_failed, name="LensFailed")


def _broken(what: str) -> nu.Nu:
    """A column saying the walk did not get there. Keeps the surface answering."""
    return nu.Literal(_failed(what))


def _column_term(
    shape_cls: type[Shape],
    cursor: tuple[str, ...],
    prefix: StructuredRef | None,
    max_rows: int,
    depth: int,
) -> nu.Nu:
    """The column for whatever ``cursor`` lands on. Protocol dispatch, in python.

    Total by construction: a segment that names nothing yields an error column
    rather than raising, so one bad crumb in a cursor does not cost the browser
    the columns to its left.
    """
    if not cursor:
        return _shape_term(shape_cls, prefix)
    try:
        ref = _descend(prefix, shape_cls, cursor)
    except Exception as exc:
        return _broken(f"{'.'.join(cursor)}: {exc!r}")
    if isinstance(ref, ShapeRef):
        return _shape_term(ref._payload["shape_type"], ref)
    if isinstance(ref, (ShapesMappingRef, MappingRef)):
        return _mapping_term(ref, max_rows, depth)
    if isinstance(ref, (ShapesSequenceRef, SequenceRef)):
        return _sequence_term(ref, max_rows, depth)
    return _leaf_term(ref)


def column_terms(
    shape: type[Shape],
    cursor: object,
    *,
    prefix: StructuredRef | None = None,
    max_rows: int = DEFAULT_MAX_ROWS,
) -> nu.Nu:
    """Every column for ``cursor``: one per prefix of it, root first.

    Full replacement, not a delta. A navigation is one frame carrying the whole
    cascade, so a browser that missed one is not left holding a stale column it
    can never be told about.

    Args:
        shape: what to expect, and what the cursor is relative to.
        cursor: segments relative to ``shape``, as a plain python sequence.
        prefix: where ``shape`` lives. None reads it at the root of its store.
        max_rows: how many rows one column ships.
    """
    steps = tuple(str(s) for s in (cursor or ()))
    cols = [_column_term(shape, steps[:i], prefix, max_rows, i) for i in range(len(steps) + 1)]
    return nu.List.of(*cols)


#: :func:`column_terms` as an atom, so the cursor can be a value the browser
#: sent. The callable is fixed at class time; the shape and the prefix ride as
#: children because they are addresses. The prefix goes in wrapped in a
#: ``Literal``: a Ref is itself a term, and an unwrapped one in a child slot
#: would be read rather than pointed at.
LensColumns = nu.host(column_terms, name="LensColumns")


def columns(
    shape: type[Shape],
    cursor: nu.Nu,
    *,
    prefix: StructuredRef | None = None,
    max_rows: int = DEFAULT_MAX_ROWS,
) -> nu.Nu:
    """The columns for a cursor nobody knew at compile time.

    ``Eval`` compiles what :data:`LensColumns` built against the running
    program and drives it in the same ctx, so the reads see the same store and
    the same fabrics as everything else in the arm. The storage boundary is the
    caller's to place: an ``Eval`` is opaque to the static effect walk, so
    nothing infers one for these reads.

    Guarded, and not as a second copy of the caller's guard: a read that raises
    inside the ``Eval`` would leave the arm with nothing to write and the
    browser waiting on a frame that never comes. A cascade always comes back,
    even if all it says is what went wrong.
    """
    return nu.TryCatch(
        nu.Eval(
            LensColumns(shape, cursor, prefix=nu.Literal(prefix), max_rows=max_rows),
            promise={"cardinality": Cardinality.SCALAR},
        ),
        catch=nu.List.of(LensFailed(nu.ToStr(nu.AttrRef("error")))),
    )
