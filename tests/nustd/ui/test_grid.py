"""Grid: equal cells, as a Shape and as Refs alone.

A Grid holds open-ended children, one per cell. Its props are its own
(max_columns, min_cell_width, dense, the layers, span); a child carries
none, not even its span. A prop ships only when set. Runs against a recording session, same harness as
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


DEFAULTS: dict[str, object] = {}


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

    props = GridRef.slot(max_columns=3, min_cell_width=200, gap=2, padding=1).props
    assert props == {"max_columns": 3, "min_cell_width": 200, "gap": 2, "padding": 1}
    with pytest.raises(ValueError, match="count"):
        GridRef.slot(max_columns="3")


def test_slot_takes_no_per_cell_props():
    from nustd.ui import GridRef

    with pytest.raises(TypeError):
        GridRef.slot(span=2)
    with pytest.raises(TypeError):
        GridRef.slot(grow={"a": 1})


def test_shape_slot_forwards_to_the_ref():
    from nustd.ui import Grid, GridRef

    class Gallery(Grid):
        pass

    assert Grid.slot().props == GridRef.slot().props
    assert (
        Gallery.slot(max_columns=3, align="start").props
        == GridRef.slot(max_columns=3, align="start").props
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
        stats = Stats.slot(max_columns=3, gap=3)

    chains = boot_chains((), Home)
    stats = [c for c in chains if c[0][0] == "stats"]
    assert [[lvl[:2] for lvl in c] for c in stats] == [
        [("stats", "Grid")],
        [("stats", "Grid"), ("users", "Card")],
        [("stats", "Grid"), ("jobs", "Card")],
        [("stats", "Grid"), ("errors", "Card")],
    ]
    assert stats[0][0][2] == {"max_columns": 3, "gap": 3}
    assert stats[2][1][2]["title"] == "Jobs"


def test_refs_alone_computed_cells_resolve_distinct_paths():
    from nustd.ui.refs import CardRef, ColumnRef, GridRef, StatRef

    page_column = ColumnRef("page")
    grid = GridRef("g", parent_ref=page_column, props={"min_cell_width": 200})
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
    assert frames[0].chain[1][2] == {"min_cell_width": 200}


def test_set_layout_writes_the_cap_only():
    from nustd.ui.refs import GridRef

    [frame] = _frames(GridRef("g").set_layout(max_columns=2))
    assert frame.op == "write"
    assert frame.ref == ("g",)
    assert frame.payload == {"max_columns": 2}
    for gone in ("set_max_columns", "set_cols", "set_rows"):
        assert not hasattr(GridRef, gone)


def test_a_grid_has_no_primary_value():
    from nustd.ui.refs import GridRef

    assert not hasattr(GridRef, "set")
    assert not hasattr(GridRef, "on_change")


def test_a_leaf_under_a_grid_still_refuses_children():
    from nustd.ui.refs import GridRef, TextRef

    cell = TextRef("caption", parent_ref=GridRef("g"))
    with pytest.raises(TypeError, match="TextRef is a leaf"):
        GridRef("inner", parent_ref=cell)


# --- span --------------------------------------------------------------------


def test_span_normalizes_to_cols_and_rows():
    from nustd.ui import GridRef

    props = GridRef.slot(
        max_columns=3, span={"hero": {"cols": 2, "rows": 2}, "wide": 3, "plain": 1}
    ).props
    assert props["span"] == {"hero": {"cols": 2, "rows": 2}, "wide": {"cols": 3, "rows": 1}}


def test_a_span_under_one_raises():
    from nustd.ui import GridRef

    with pytest.raises(ValueError, match="at least 1 by 1"):
        GridRef.slot(span={"x": {"cols": 0}})


def test_a_bento_shape_spans_by_slot_name():
    from nustd.ui import CardRef, Column, Grid

    class Bento(Grid):
        revenue = CardRef.slot(title="Revenue")
        users = CardRef.slot(title="Users")
        jobs = CardRef.slot(title="Jobs")

    class Home(Column):
        bento = Bento.slot(max_columns=3, dense=True, span={"revenue": {"cols": 2, "rows": 2}})

    [grid, *cells] = [c for c in boot_chains((), Home) if c[0][0] == "bento"]
    assert grid[0][2]["span"] == {"revenue": {"cols": 2, "rows": 2}}
    assert grid[0][2]["dense"] is True
    # The cell itself carries nothing about its span.
    assert "span" not in cells[0][1][2]
    assert "spans" not in cells[0][1][2]


def test_set_child_span_by_key_ships_its_own_op():
    from nustd.ui.refs import GridRef

    [frame] = _frames(GridRef("g").set_child("hero", span={"cols": 2, "rows": 2}))
    assert frame.op == "set_child"
    assert frame.ref == ("g",)
    assert frame.payload == {"key": "hero", "span": {"cols": 2, "rows": 2}}
    assert _chain(frame) == [("g", "Grid")]


def test_set_child_takes_a_child_ref_and_a_computed_key():
    from nustd.ui.refs import CardRef, GridRef

    grid = GridRef("g")
    card = CardRef(nu.Str("c") + nu.str(2), parent_ref=grid)
    [by_ref, by_term] = _frames(
        grid.set_child(card, span=3) >> grid.set_child(nu.Str("c") + nu.str(1), span=2)
    )
    assert by_ref.payload == {"key": "c2", "span": {"cols": 3, "rows": 1}}
    assert by_term.payload == {"key": "c1", "span": {"cols": 2, "rows": 1}}


# --- placed: a track template, cells at (r, c) ------------------------------


def test_placed_cell_sits_at_r_comma_c():
    from nustd.ui import GridRef, TextRef

    g = GridRef("g", props={"cols": "2fr 1fr"})
    [frame] = _frames(g[1, 0].to(TextRef).set("x"))
    assert frame.ref == ("g", "1,0")
    assert _chain(frame) == [("g", "Grid"), ("1,0", "TextRef")]
    assert frame.chain[0][2]["cols"] == "2fr 1fr"


def test_placed_cell_by_method_and_computed_place():
    from nustd.ui import GridRef, TextRef

    g = GridRef("g", props={"cols": 2})
    assert g.cell(0, 1)._payload["segment"] == "0,1"
    [frame] = _frames(g[nu.Int(2), 1].to(TextRef).set("x"))
    assert frame.ref == ("g", "2,1")


def test_placed_cell_takes_the_item_default():
    from nustd.ui import CardRef, GridRef

    g = GridRef("g", item=CardRef.slot(title="T"), props={"cols": "1fr 1fr"})
    cell = g[0, 0]
    assert type(cell) is CardRef
    [frame] = _frames(cell.set_title("x"))
    assert _chain(frame) == [("g", "Grid"), ("0,0", "Card")]


def test_placed_cell_without_a_template_is_refused():
    from nustd.ui import GridRef

    with pytest.raises(TypeError, match="track template"):
        GridRef("g", props={"max_columns": 3})[0, 1]
    with pytest.raises(TypeError, match="track template"):
        GridRef("g")[0, 1]


@pytest.mark.parametrize(
    ("at", "error"),
    [
        ((0, "a"), TypeError),
        ((-1, 0), IndexError),
        ((True, 0), TypeError),
        ((0, 0, 0), TypeError),
        ((None, 0), TypeError),
    ],
)
def test_placed_keys_are_positions_only(at, error):
    from nustd.ui import GridRef

    with pytest.raises(error):
        GridRef("g", props={"cols": "1fr 1fr"})[at]


def test_a_name_that_reads_as_a_place_is_refused():
    from nustd.ui import GridRef

    with pytest.raises(ValueError, match=r"grid\[r, c\]"):
        GridRef("g", props={"cols": "1fr"})["0,1"]


def test_flow_keys_still_work_on_a_placed_grid():
    from nustd.ui import GridRef, TextRef

    g = GridRef("g", props={"cols": "1fr 1fr"})
    [a, b] = _frames(g["note"].to(TextRef).set("n") >> g[0].to(TextRef).set("z"))
    assert a.ref == ("g", "note")
    assert b.ref == ("g", "0")


def test_track_templates_normalize():
    from nustd.ui import GridRef

    props = GridRef.slot(
        cols=[240, "1fr", "minmax(0, 2fr)"], rows=[64, "auto"], stack_below=640
    ).props
    assert props["cols"] == "240px 1fr minmax(0, 2fr)"
    assert props["rows"] == "64px auto"
    assert props["stack_below"] == 640
    assert GridRef.slot(cols=3).props["cols"] == "repeat(3, minmax(0, 1fr))"
    assert GridRef.slot(cols="  2fr   1fr ").props["cols"] == "2fr 1fr"
    assert "rows" not in GridRef.slot(cols=2).props


def test_a_flow_grid_ships_nothing_unset():
    from nustd.ui import GridRef

    assert GridRef.slot().props == DEFAULTS


def test_placed_grid_ships_no_flow_props():
    from nustd.ui import GridRef

    props = GridRef.slot(cols="2fr 1fr", rows=2).props
    assert props == {"cols": "2fr 1fr", "rows": "repeat(2, minmax(0, 1fr))"}


@pytest.mark.parametrize("flow", [{"max_columns": 3}, {"min_cell_width": 200}])
def test_placed_grid_refuses_flow_props(flow):
    from nustd.ui import GridRef

    with pytest.raises(ValueError, match="size a flowing grid"):
        GridRef.slot(cols="1fr 1fr", **flow)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cols": "1fr; color: red"},
        {"cols": "url(x)"},
        {"cols": 0},
        {"cols": ""},
        {"rows": "1fr"},
        {"stack_below": 400},
        {"span": {(0, 0): 2}},
    ],
)
def test_bad_templates_are_refused(kwargs):
    from nustd.ui import GridRef

    with pytest.raises((ValueError, TypeError)):
        GridRef.slot(**kwargs)


def test_placed_span_keys_by_place():
    from nustd.ui import GridRef

    props = GridRef.slot(cols="2fr 1fr", span={(0, 0): 2, (1, 1): 1, "note": 2}).props
    assert props["span"] == {"0,0": {"cols": 2, "rows": 1}, "note": {"cols": 2, "rows": 1}}


def test_set_child_takes_a_place():
    from nustd.ui import GridRef

    g = GridRef("g", props={"cols": "1fr 1fr"})
    [frame] = _frames(g.set_child((1, 0), span={"cols": 2, "rows": 2}))
    assert frame.payload == {"key": "1,0", "span": {"cols": 2, "rows": 2}}
    [by_ref] = _frames(g.set_child(g[0, 1], span=2))
    assert by_ref.payload["key"] == "0,1"
    with pytest.raises(TypeError, match="track template"):
        GridRef("f").set_child((0, 1), span=2)


def test_set_layout_writes_templates_and_family_props():
    from nustd.ui import GridRef

    [frame] = _frames(GridRef("g").set_layout(cols=[200, "1fr"], rows=2, stack_below=640))
    assert frame.payload == {
        "cols": "200px 1fr",
        "rows": "repeat(2, minmax(0, 1fr))",
        "stack_below": 640,
    }
    [flow] = _frames(GridRef("g").set_layout(min_cell_width=160, dense=True, gap=2))
    assert flow.payload == {"min_cell_width": 160, "dense": True, "gap": 2}
    with pytest.raises(ValueError, match="size a flowing grid"):
        GridRef("g").set_layout(cols=2, max_columns=3)
    with pytest.raises(ValueError, match="not a track template"):
        GridRef("g").set_layout(cols="2fr; color: red")


def test_a_placed_shape_grid():
    from nustd.ui import Grid

    class Board(Grid):
        pass

    slot = Board.slot(cols="2fr 1fr")
    assert slot.props["cols"] == "2fr 1fr"


def test_grid_takes_height_and_scroll():
    from nustd.ui import GridRef

    props = GridRef.slot(height=320, scroll="y").props
    assert props["height"] == 320
    assert props["scroll"] == "y"
