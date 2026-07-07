"""Tests for the ``Provide`` bracket family.

Two dimensions: attach shape (one / list / dict) and tag/predicate knobs.
The bracket owns construction, setup ordering, LIFO teardown, and
tag+predicate threading into Context. Tests keep instances observable via a
shared list; each pass wipes them.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from nu.context import FabricRef, Provide, ProvideDict, ProvideList
from nu.lang import Context
from nu.lang.helpers import arun, run


class Counter:
    """Trivial fabric; setup/cleanup log to a shared list."""

    events: ClassVar[list[tuple[str, str]]] = []

    def __init__(self, name: str) -> None:
        self.name = name

    def setup(self, ctx: Context) -> None:
        Counter.events.append(("setup", self.name))

    def cleanup(self) -> None:
        Counter.events.append(("close", self.name))


@pytest.fixture(autouse=True)
def _reset_events() -> None:
    Counter.events.clear()


# --- single Provide ------------------------------------------------------


def test_provide_binds_by_type_and_runs_body():
    value, _ = run(Provide(Counter, {"name": "a"}, FabricRef(Counter)))
    assert isinstance(value, Counter)
    assert value.name == "a"


def test_provide_teardown_fires_lifo_on_exit():
    run(Provide(Counter, {"name": "a"}, FabricRef(Counter)))
    assert Counter.events == [("setup", "a"), ("close", "a")]


def test_provide_tag_sugar_binds_under_that_tag():
    class Store:
        pass

    bracket = Provide(Store, {}, FabricRef(Store), tag="alpha")
    with bracket._open(Context()) as ctx:
        assert ctx.has(Store, "alpha")
        assert not ctx.has(Store, "beta")


def test_provide_tags_multi_bind_requires_full_tag_set():
    class Store:
        pass

    # Multi-tag is AND: the lookup key is the full frozenset of tags.
    # Subset resolution runs the OTHER way (a more-specific request falls
    # back to a less-specific binding), never a less-specific request
    # matching a more-specific binding.
    bracket = Provide(Store, {}, FabricRef(Store), tags=("gpu", "worker"))
    with bracket._open(Context()) as ctx:
        inst = ctx.get(Store, "gpu", "worker")
        assert inst is not None
        # A more-specific request falls back to this binding as the closest match.
        assert ctx.get(Store, "gpu", "worker", "extra") is inst
        # A single-tag request without the other tag does NOT match.
        with pytest.raises(LookupError):
            ctx.get(Store, "gpu")


def test_provide_tag_and_tags_compose_into_one_tuple():
    class Store:
        pass

    bracket = Provide(Store, {}, FabricRef(Store), tag="primary", tags=("gpu",))
    with bracket._open(Context()) as ctx:
        inst = ctx.get(Store, "primary", "gpu")
        assert inst is not None
        # Order of tags at lookup does not matter (frozenset).
        assert ctx.get(Store, "gpu", "primary") is inst


def test_provide_predicate_forwards_to_ctx_bind():
    class Store:
        def __init__(self) -> None:
            self.owner = "unset"

    # Inline body reading through a plain Python bracket: build the bracket
    # + open its _open manually to inspect ctx state.
    def match_site(site: int) -> bool:
        return site < 5

    bracket = Provide(Store, {}, FabricRef(Store), predicate=match_site)
    with bracket._open(Context()) as ctx:
        # Predicate binding lives in _guarded, not _entries.
        assert not ctx.has(Store)  # no data kwargs -> nothing to match
        assert ctx.get(Store, site=3) is not None
        with pytest.raises(LookupError):
            ctx.get(Store, site=10)


# --- ProvideList ---------------------------------------------------------


def test_provide_list_binds_each_by_index():
    class Store:
        def __init__(self, i: int) -> None:
            self.i = i

    bracket = ProvideList(
        Store, [{"i": 0}, {"i": 1}, {"i": 2}], FabricRef(Store), base_tag=10
    )
    with bracket._open(Context()) as ctx:
        assert ctx.get(Store, 10).i == 0
        assert ctx.get(Store, 11).i == 1
        assert ctx.get(Store, 12).i == 2


def test_provide_list_extra_tags_share_across_fleet():
    class Store:
        def __init__(self, i: int) -> None:
            self.i = i

    bracket = ProvideList(
        Store, [{"i": 0}, {"i": 1}], FabricRef(Store), extra_tags=("worker",)
    )
    with bracket._open(Context()) as ctx:
        # index + shared extra tag both address the same binding.
        assert ctx.get(Store, 0, "worker").i == 0
        assert ctx.get(Store, 1, "worker").i == 1


def test_provide_list_teardown_is_lifo():
    run(
        ProvideList(
            Counter,
            [{"name": "a"}, {"name": "b"}, {"name": "c"}],
            FabricRef(Counter),
        )
    )
    setups = [n for kind, n in Counter.events if kind == "setup"]
    closes = [n for kind, n in Counter.events if kind == "close"]
    assert setups == ["a", "b", "c"]
    assert closes == ["c", "b", "a"]


def test_provide_list_partial_setup_failure_tears_down_completed():
    class Flaky:
        events: ClassVar[list[str]] = []

        def __init__(self, i: int, boom: bool = False) -> None:
            self.i = i
            self.boom = boom

        def setup(self, ctx: Context) -> None:
            if self.boom:
                raise RuntimeError(f"boom {self.i}")
            Flaky.events.append(f"setup:{self.i}")

        def cleanup(self) -> None:
            Flaky.events.append(f"close:{self.i}")

    bracket = ProvideList(
        Flaky,
        [{"i": 0}, {"i": 1}, {"i": 2, "boom": True}, {"i": 3}],
        FabricRef(Flaky),
    )
    with pytest.raises(RuntimeError, match="boom 2"):
        run(bracket)
    assert Flaky.events == ["setup:0", "setup:1", "close:1", "close:0"]


# --- ProvideDict ---------------------------------------------------------


def test_provide_dict_binds_each_by_key():
    class Store:
        def __init__(self, name: str) -> None:
            self.name = name

    bracket = ProvideDict(
        Store,
        {"gpu": {"name": "g"}, "cpu": {"name": "c"}},
        FabricRef(Store),
    )
    with bracket._open(Context()) as ctx:
        assert ctx.get(Store, "gpu").name == "g"
        assert ctx.get(Store, "cpu").name == "c"


def test_provide_dict_extra_tags_share_across_fleet():
    class Store:
        def __init__(self, name: str) -> None:
            self.name = name

    bracket = ProvideDict(
        Store,
        {"gpu": {"name": "g"}, "cpu": {"name": "c"}},
        FabricRef(Store),
        extra_tags=("shard",),
    )
    with bracket._open(Context()) as ctx:
        assert ctx.get(Store, "gpu", "shard").name == "g"
        assert ctx.get(Store, "cpu", "shard").name == "c"


# --- async lifecycle -----------------------------------------------------


async def test_provide_prefers_asetup_when_defined():
    class AsyncStore:
        events: ClassVar[list[str]] = []

        def __init__(self) -> None:
            self.name = "x"

        async def asetup(self, ctx: Context) -> None:
            AsyncStore.events.append("asetup")

        async def acleanup(self) -> None:
            AsyncStore.events.append("acleanup")

    value, _ = await arun(Provide(AsyncStore, {}, FabricRef(AsyncStore)))
    assert isinstance(value, AsyncStore)
    assert AsyncStore.events == ["asetup", "acleanup"]


# --- DI through ctx.get in setup -----------------------------------------


def test_inner_provide_reads_outer_binding_via_ctx_get():
    class Codec:
        def __init__(self, kind: str) -> None:
            self.kind = kind

    class Storage:
        def __init__(self) -> None:
            self.codec_kind: str | None = None

        def setup(self, ctx: Context) -> None:
            self.codec_kind = ctx.get(Codec).kind

    app = Provide(Codec, {"kind": "json"}, Provide(Storage, {}, FabricRef(Storage)))
    value, _ = run(app)
    assert isinstance(value, Storage) and value.codec_kind == "json"
