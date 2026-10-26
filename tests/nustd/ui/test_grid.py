"""Grid: equal cells, as a Shape and as Refs alone.

A Grid holds open-ended children, one per cell. Its props are its own
(columns, min_width, gap, align, padding, dense, spans); a child carries
none, not even its span. Runs against a recording session, same harness as
test_layers.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd.ui import Session
from nustd.ui.core.base import _wire_type_of
from nustd.ui.core.chains import boot_chains


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _frames(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _chain(frame):
    return [(seg, typ) for seg, typ, _ in frame.chain]


DEFAULTS = {
    "columns": 0,
    "min_width": 240,
    "gap": 4,
    "align": "stretch",
    "padding": 0,
    "dense": False,
    "spans": {},
}


def test_grid_is_a_container_with_its_own_wire_type():
    from nustd.ui import Grid, GridRef
    from nustd.ui.refs import CollectionRef

    assert issubclass(GridRef, CollectionRef)
    assert GridRef._wire_type == "Grid"
    assert Grid._ref_cls is GridRef
    assert "_wire_type" not in vars(Grid)
    assert "slot" not in vars(Grid)
    assert _wire_type_of(Grid) == "Grid"


def test_slot_defaults():
    from nustd.ui import GridRef

    assert GridRef.slot().props == DEFAULTS


def test_slot_coerces_the_numbers():
    from nustd.ui import GridRef

    props = GridRef.slot(columns="3", min_width=200.0, gap="2", padding="1").props
    assert props == {**DEFAULTS, "columns": 3, "min_width": 200, "gap": 2, "padding": 1}


def test_slot_takes_no_per_cell_props():
    from nustd.ui import GridRef

    with pytest.raises(TypeError):
        GridRef.slot(span=2)


def test_shape_slot_forwards_to_the_ref():
    from nustd.ui import Grid, GridRef

    class Gallery(Grid):
        pass

    assert Grid.slot().props == GridRef.slot().props
    assert (
        Gallery.slot(columns=3, align="start").props == GridRef.slot(columns=3, align="start").props
    )
    assert Gallery.slot().ref_cls is GridRef
    assert Gallery.slot().kwargs["section_cls"] is Gallery


def test_boot_chains_of_a_page_with_a_grid_of_cards():
    from nustd.ui import CardRef, Column, Grid

    class Stats(Grid):
        users = CardRef.slot(title="Users")
        jobs = CardRef.slot(title="Jobs")
        errors = CardRef.slot(title="Errors")

    class Home(Column):
        stats = Stats.slot(columns=3, gap=3)

    chains = boot_chains((), Home)
    stats = [c for c in chains if c[0][0] == "stats"]
    assert [[lvl[:2] for lvl in c] for c in stats] == [
        [("stats", "Grid")],
        [("stats", "Grid"), ("users", "Card")],
        [("stats", "Grid"), ("jobs", "Card")],
        [("stats", "Grid"), ("errors", "Card")],
    ]
    assert stats[0][0][2] == {**DEFAULTS, "columns": 3, "gap": 3}
    assert stats[2][1][2]["title"] == "Jobs"


def test_refs_alone_computed_cells_resolve_distinct_paths():
    from nustd.ui.refs import CardRef, ColumnRef, GridRef, StatRef

    page_column = ColumnRef("page")
    grid = GridRef("g", parent_ref=page_column, props={"min_width": 200})
    writes = [
        StatRef("s", parent_ref=CardRef(nu.Str("c") + nu.str(i), parent_ref=grid)).set(str(i))
        for i in range(3)
    ]
    frames = _frames(writes[0] >> writes[1] >> writes[2])
    assert [f.ref for f in frames] == [("page", "g", f"c{i}", "s") for i in range(3)]
    assert _chain(frames[1]) == [
        ("page", "Column"),
        ("g", "Grid"),
        ("c1", "Card"),
        ("s", "StatRef"),
    ]
    assert frames[0].chain[1][2] == {**DEFAULTS, "min_width": 200}


def test_set_columns_writes_columns_only():
    from nustd.ui.refs import GridRef

    [frame] = _frames(GridRef("g").set_columns(2))
    assert frame.op == "write"
    assert frame.ref == ("g",)
    assert frame.payload == {"columns": 2}


def test_a_grid_has_no_primary_value():
    from nustd.ui.refs import GridRef

    assert not hasattr(GridRef, "set")
    assert not hasattr(GridRef, "on_change")


def test_a_leaf_under_a_grid_still_refuses_children():
    from nustd.ui.refs import GridRef, TextRef

    cell = TextRef("caption", parent_ref=GridRef("g"))
    with pytest.raises(TypeError, match="TextRef is a leaf"):
        GridRef("inner", parent_ref=cell)


# --- spans -------------------------------------------------------------------


def test_spans_normalize_to_cols_and_rows():
    from nustd.ui import GridRef

    props = GridRef.slot(columns=3, spans={"hero": (2, 2), "wide": 3, "plain": 1}).props
    assert props["spans"] == {"hero": {"cols": 2, "rows": 2}, "wide": {"cols": 3, "rows": 1}}


def test_a_span_under_one_raises():
    from nustd.ui import GridRef

    with pytest.raises(ValueError, match="at least 1 by 1"):
        GridRef.slot(spans={"x": (0, 1)})


def test_a_bento_shape_spans_by_slot_name():
    from nustd.ui import CardRef, Column, Grid

    class Bento(Grid):
        revenue = CardRef.slot(title="Revenue")
        users = CardRef.slot(title="Users")
        jobs = CardRef.slot(title="Jobs")

    class Home(Column):
        bento = Bento.slot(columns=3, dense=True, spans={"revenue": (2, 2)})

    [grid, *cells] = [c for c in boot_chains((), Home) if c[0][0] == "bento"]
    assert grid[0][2]["spans"] == {"revenue": {"cols": 2, "rows": 2}}
    assert grid[0][2]["dense"] is True
    # The cell itself carries nothing about its span.
    assert "span" not in cells[0][1][2]
    assert "spans" not in cells[0][1][2]


def test_set_span_by_key_ships_its_own_op():
    from nustd.ui.refs import GridRef

    [frame] = _frames(GridRef("g").set_span("hero", 2, 2))
    assert frame.op == "set_span"
    assert frame.ref == ("g",)
    assert frame.payload == {"key": "hero", "cols": 2, "rows": 2}
    assert _chain(frame) == [("g", "Grid")]


def test_set_span_takes_a_child_ref_and_a_computed_key():
    from nustd.ui.refs import CardRef, GridRef

    grid = GridRef("g")
    card = CardRef(nu.Str("c") + nu.str(2), parent_ref=grid)
    [by_ref, by_term] = _frames(grid.set_span(card, 3) >> grid.set_span(nu.Str("c") + nu.str(1), 2))
    assert by_ref.payload == {"key": "c2", "cols": 3, "rows": 1}
    assert by_term.payload == {"key": "c1", "cols": 2, "rows": 1}
