"""Grid: equal cells, as a Shape and as Refs alone.

A Grid holds open-ended children, one per cell. Its props are its own
(columns, min_width, gap, align, padding); a child carries none. Runs
against a recording session, same harness as test_layers.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd.ui import Session
from nustd.ui.core.base import _wire_type_of


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


DEFAULTS = {"columns": 0, "min_width": 240, "gap": 4, "align": "stretch", "padding": 0}


def test_grid_is_a_container_with_its_own_wire_type():
    from nustd.ui import Grid, GridRef
    from nustd.ui.refs import ContainerRef

    assert issubclass(GridRef, ContainerRef)
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
    from nustd.ui import CardRef, Grid
    from nustd.ui.nudle import Page

    class Stats(Grid):
        users = CardRef.slot(title="Users")
        jobs = CardRef.slot(title="Jobs")
        errors = CardRef.slot(title="Errors")

    class Home(Page):
        stats = Stats.slot(columns=3, gap=3)

    chains = Home._boot_chains()
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
