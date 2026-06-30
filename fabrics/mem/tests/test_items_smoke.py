"""Smoke test for the v2 mem substrate foundation: single-level item refs.

Proves RefBase end-to-end against the real runtime: read (dual role), write
through the ref (vivifying the container), and the missing-key EMPTY sentinel,
sync and async. Imports the item refs directly (the full nu_mem package has
unported modules during the P2 port).
"""

from __future__ import annotations

import pytest

from nu import EMPTY, Context, LiteralQuery, arun, run
from nu.domains.shape import Shape
from nu_mem import (
    DictRef,
    FloatRef,
    IntRef,
    ListRef,
    SetRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
)


class UserShape(Shape):
    name = StrRef.slot()
    age = IntRef.slot()
    score = FloatRef.slot()


class PortfolioShape(Shape):
    tags = ListRef.slot(str)
    metadata = DictRef.slot(str)
    members = SetRef.slot(str)


class TeamShape(Shape):
    name = StrRef.slot()
    info = ShapeRef.slot(UserShape)
    members = ShapesDictRef.slot(UserShape)
    roster = ShapesListRef.slot(UserShape)


def _ctx(data: dict) -> Context:
    return Context().bind(dict, data, UserShape)


def test_read_existing_value() -> None:
    data = {"name": "alice", "age": 30, "score": 9.5}
    ctx = _ctx(data)
    assert run(UserShape.name, ctx)[0] == "alice"
    assert run(UserShape.age, ctx)[0] == 30
    assert run(UserShape.score, ctx)[0] == 9.5


def test_read_missing_returns_empty() -> None:
    ctx = _ctx({})
    assert run(UserShape.name, ctx)[0] is EMPTY


def test_write_then_read() -> None:
    data: dict = {}
    ctx = _ctx(data)
    run(UserShape.name.store(LiteralQuery("bob")), ctx)
    assert data["name"] == "bob"
    assert run(UserShape.name, ctx)[0] == "bob"


async def test_read_and_write_async() -> None:
    data: dict = {"age": 1}
    ctx = _ctx(data)
    assert (await arun(UserShape.age, ctx))[0] == 1
    await arun(UserShape.name.store(LiteralQuery("zed")), ctx)
    assert data["name"] == "zed"


@pytest.mark.parametrize("missing", ["name", "score"])
def test_missing_each_field(missing: str) -> None:
    ctx = _ctx({})
    ref = getattr(UserShape, missing)
    assert run(ref, ctx)[0] is EMPTY


# --- set collection ref ---------------------------------------------------


def _pf_ctx(data: dict) -> Context:
    return Context().bind(dict, data, PortfolioShape)


def test_set_ref_reads_container() -> None:
    ctx = _pf_ctx({"members": {"alice", "bob"}})
    assert run(PortfolioShape.members, ctx)[0] == {"alice", "bob"}


def test_set_ref_len_op() -> None:
    ctx = _pf_ctx({"members": {"alice", "bob", "carol"}})
    assert run(PortfolioShape.members.len(), ctx)[0] == 3


def test_set_ref_store_then_read() -> None:
    data: dict = {}
    ctx = _pf_ctx(data)
    run(PortfolioShape.members.store(LiteralQuery({"x", "y"})), ctx)
    assert data["members"] == {"x", "y"}


# --- list collection ref --------------------------------------------------


def test_list_ref_reads_container() -> None:
    ctx = _pf_ctx({"tags": ["a", "b", "c"]})
    assert run(PortfolioShape.tags, ctx)[0] == ["a", "b", "c"]


def test_list_ref_len_and_store() -> None:
    data: dict = {"tags": ["a", "b"]}
    ctx = _pf_ctx(data)
    assert run(PortfolioShape.tags.len(), ctx)[0] == 2
    run(PortfolioShape.tags.store(LiteralQuery(["x"])), ctx)
    assert data["tags"] == ["x"]


# --- dict (mapping) collection ref ----------------------------------------


def test_dict_ref_reads_container() -> None:
    ctx = _pf_ctx({"metadata": {"risk": "low"}})
    assert run(PortfolioShape.metadata, ctx)[0] == {"risk": "low"}


def test_dict_ref_keys_and_get() -> None:
    ctx = _pf_ctx({"metadata": {"risk": "low", "strat": "momentum"}})
    assert set(run(PortfolioShape.metadata.keys(), ctx)[0]) == {"risk", "strat"}
    assert run(PortfolioShape.metadata.get("risk"), ctx)[0] == "low"


def test_dict_ref_store() -> None:
    data: dict = {}
    ctx = _pf_ctx(data)
    run(PortfolioShape.metadata.store(LiteralQuery({"k": "v"})), ctx)
    assert data["metadata"] == {"k": "v"}


# --- shape + shapes-collection refs ---------------------------------------


def _team_ctx(data: dict) -> Context:
    return Context().bind(dict, data, TeamShape)


def test_shape_field_navigation() -> None:
    # info.field rides the substrate: blueprint __getattr__ -> mem field ref.
    ctx = _team_ctx({"info": {"name": "ann", "age": 5}})
    assert run(TeamShape.info.name, ctx)[0] == "ann"
    assert run(TeamShape.info.age, ctx)[0] == 5


def test_shape_keys() -> None:
    ctx = _team_ctx({"info": {"name": "ann", "age": 5}})
    assert set(run(TeamShape.info.keys(), ctx)[0]) == {"name", "age"}


def test_shapesdict_keys() -> None:
    ctx = _team_ctx({"members": {"alice": {"name": "a"}, "bob": {"name": "b"}}})
    assert set(run(TeamShape.members.keys(), ctx)[0]) == {"alice", "bob"}


def test_shapeslist_len() -> None:
    ctx = _team_ctx({"roster": [{"name": "x"}, {"name": "y"}]})
    assert run(TeamShape.roster.len(), ctx)[0] == 2
