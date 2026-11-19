"""Tests for the ``Provide`` bracket family.

Two dimensions: attach shape (one / list / dict) and tag/predicate knobs.
The bracket owns construction, setup ordering, LIFO teardown, and
tag+predicate threading into Context. Tests keep instances observable via a
shared list; each pass wipes them.
"""

from __future__ import annotations

import asyncio
from typing import ClassVar

import pytest
from _support.brackets import config

import nu
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
    ctx = Context()
    with bracket._enter(ctx):
        assert ctx.fabrics.has(Store, "alpha")
        assert not ctx.fabrics.has(Store, "beta")


def test_provide_tags_multi_bind_requires_full_tag_set():
    class Store:
        pass

    # Multi-tag is AND: the lookup key is the full frozenset of tags.
    # Subset resolution runs the OTHER way (a more-specific request falls
    # back to a less-specific binding), never a less-specific request
    # matching a more-specific binding.
    bracket = Provide(Store, {}, FabricRef(Store), tags=("gpu", "worker"))
    ctx = Context()
    with bracket._enter(ctx):
        inst = ctx.fabrics.get(Store, "gpu", "worker")
        assert inst is not None
        # A more-specific request falls back to this binding as the closest match.
        assert ctx.fabrics.get(Store, "gpu", "worker", "extra") is inst
        # A single-tag request without the other tag does NOT match.
        with pytest.raises(LookupError):
            ctx.fabrics.get(Store, "gpu")


def test_provide_tag_and_tags_compose_into_one_tuple():
    class Store:
        pass

    bracket = Provide(Store, {}, FabricRef(Store), tag="primary", tags=("gpu",))
    ctx = Context()
    with bracket._enter(ctx):
        inst = ctx.fabrics.get(Store, "primary", "gpu")
        assert inst is not None
        # Order of tags at lookup does not matter (frozenset).
        assert ctx.fabrics.get(Store, "gpu", "primary") is inst


def test_provide_predicate_forwards_to_ctx_bind():
    class Store:
        def __init__(self) -> None:
            self.owner = "unset"

    # Inline body reading through a plain Python bracket: build the bracket
    # + open its _open manually to inspect ctx state.
    def match_site(site: int) -> bool:
        return site < 5

    bracket = Provide(Store, {}, FabricRef(Store), predicate=match_site)
    ctx = Context()
    with bracket._enter(ctx):
        # A predicate binding resolves only against data.
        assert not ctx.fabrics.has(Store)  # no data kwargs -> nothing to match
        assert ctx.fabrics.get(Store, site=3) is not None
        with pytest.raises(LookupError):
            ctx.fabrics.get(Store, site=10)


# --- ProvideList ---------------------------------------------------------


def test_provide_list_binds_each_by_index():
    class Store:
        def __init__(self, i: int) -> None:
            self.i = i

    bracket = ProvideList(Store, [{"i": 0}, {"i": 1}, {"i": 2}], FabricRef(Store), base_tag=10)
    ctx = Context()
    with bracket._enter(ctx):
        assert ctx.fabrics.get(Store, 10).i == 0
        assert ctx.fabrics.get(Store, 11).i == 1
        assert ctx.fabrics.get(Store, 12).i == 2


def test_provide_list_extra_tags_share_across_fleet():
    class Store:
        def __init__(self, i: int) -> None:
            self.i = i

    bracket = ProvideList(Store, [{"i": 0}, {"i": 1}], FabricRef(Store), extra_tags=("worker",))
    ctx = Context()
    with bracket._enter(ctx):
        # index + shared extra tag both address the same binding.
        assert ctx.fabrics.get(Store, 0, "worker").i == 0
        assert ctx.fabrics.get(Store, 1, "worker").i == 1


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
    ctx = Context()
    with bracket._enter(ctx):
        assert ctx.fabrics.get(Store, "gpu").name == "g"
        assert ctx.fabrics.get(Store, "cpu").name == "c"


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
    ctx = Context()
    with bracket._enter(ctx):
        assert ctx.fabrics.get(Store, "gpu", "shard").name == "g"
        assert ctx.fabrics.get(Store, "cpu", "shard").name == "c"


async def test_provide_dict_parallel_failure_cancels_siblings_and_tears_down_the_done():
    # One setup fails: the slow sibling is cancelled and finishes unwinding,
    # and the one whose setup already finished gets its teardown.
    events: list[str] = []

    class Member:
        def __init__(self, k: str) -> None:
            self.k = k

        async def asetup(self, ctx: Context) -> None:
            if self.k == "fast":
                events.append("setup:fast")
                return
            if self.k == "bad":
                await asyncio.sleep(0.01)
                msg = "bad setup"
                raise RuntimeError(msg)
            try:
                await asyncio.Event().wait()
            finally:
                await asyncio.sleep(0.02)
                events.append("unwound:slow")

        async def acleanup(self) -> None:
            events.append(f"close:{self.k}")

    bracket = ProvideDict(
        Member,
        {"fast": {"k": "fast"}, "slow": {"k": "slow"}, "bad": {"k": "bad"}},
        FabricRef(Member),
        parallel=True,
    )
    with pytest.raises(RuntimeError, match="bad setup"):
        await arun(bracket)
    assert events == ["setup:fast", "unwound:slow", "close:fast"]


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
            self.codec_kind = ctx.fabrics.get(Codec).kind

    app = Provide(Codec, {"kind": "json"}, Provide(Storage, {}, FabricRef(Storage)))
    value, _ = run(app)
    assert isinstance(value, Storage) and value.codec_kind == "json"


# --- async-only marker + sync-setup safety net ---------------------------


def test_provide_refuses_async_only_marker_under_sync_open():
    class AsyncOnly:
        _nu_async_only = True

        async def asetup(self, ctx: Context) -> None: ...
        async def acleanup(self) -> None: ...

    with pytest.raises(RuntimeError, match="_nu_async_only"):
        run(Provide(AsyncOnly, {}, FabricRef(AsyncOnly)))


async def test_provide_async_only_marker_does_not_gate_arun():
    class AsyncOnly:
        _nu_async_only = True
        events: ClassVar[list[str]] = []

        async def asetup(self, ctx: Context) -> None:
            AsyncOnly.events.append("asetup")

        async def acleanup(self) -> None:
            AsyncOnly.events.append("acleanup")

    AsyncOnly.events.clear()
    await arun(Provide(AsyncOnly, {}, FabricRef(AsyncOnly)))
    assert AsyncOnly.events == ["asetup", "acleanup"]


def test_provide_raises_when_instance_has_only_asetup():
    class HalfAsync:
        async def asetup(self, ctx: Context) -> None: ...
        async def acleanup(self) -> None: ...

    with pytest.raises(RuntimeError, match="no sync setup"):
        run(Provide(HalfAsync, {}, FabricRef(HalfAsync)))


def test_provide_list_refuses_async_only_marker_under_sync_open():
    class AsyncOnly:
        _nu_async_only = True

        def __init__(self, i: int) -> None:
            self.i = i

        async def asetup(self, ctx: Context) -> None: ...
        async def acleanup(self) -> None: ...

    with pytest.raises(RuntimeError, match="_nu_async_only"):
        run(ProvideList(AsyncOnly, [{"i": 0}], FabricRef(AsyncOnly)))


def test_provide_dict_refuses_async_only_marker_under_sync_open():
    class AsyncOnly:
        _nu_async_only = True

        def __init__(self, k: str) -> None:
            self.k = k

        async def asetup(self, ctx: Context) -> None: ...
        async def acleanup(self) -> None: ...

    with pytest.raises(RuntimeError, match="_nu_async_only"):
        run(ProvideDict(AsyncOnly, {"a": {"k": "a"}}, FabricRef(AsyncOnly)))


# --- config is children ----------------------------------------------------


class Cfg(nu.Shape):
    """Mem slots a tree reads a Provide's config from."""

    kwargs = nu.DictRef.slot(nu.StrRef)
    first = nu.DictRef.slot(nu.StrRef)
    second = nu.DictRef.slot(nu.StrRef)
    runs = nu.IntRef.slot()


def test_provide_config_sits_after_the_body_as_children():
    body = FabricRef(Counter)
    bracket = Provide(Counter, {"name": "a"}, body, tag="t")
    head, cls, kwargs, tags, predicate, bind_as = nu.tree.children(bracket)
    assert head is body
    assert [c.value for c in (cls, predicate, bind_as)] == [Counter, None, None]
    # kwargs and tags are built field by field, each one a child of its own.
    assert [c.value for c in nu.tree.children(kwargs)] == ["a"]
    assert [c.value for c in nu.tree.children(tags)] == ["t"]
    assert config(bracket) == {
        "cls": Counter,
        "kwargs": {"name": "a"},
        "tags": ("t",),
        "predicate": None,
        "bind_as": None,
    }


def test_provide_kwargs_come_from_a_mem_read():
    tree = nu.Frame(
        Cfg, Provide(Counter, Cfg.kwargs, FabricRef(Counter)), kwargs={"name": "from-mem"}
    )
    value, _ = run(tree)
    assert value.name == "from-mem"
    assert Counter.events == [("setup", "from-mem"), ("close", "from-mem")]


async def test_provide_kwargs_come_from_a_mem_read_async():
    tree = nu.Frame(
        Cfg, Provide(Counter, Cfg.kwargs, FabricRef(Counter)), kwargs={"name": "from-mem"}
    )
    value, _ = await arun(tree)
    assert value.name == "from-mem"


def test_provide_list_specs_come_from_a_computation():
    specs = nu.Collect(nu.Iter([{"name": "x"}, {"name": "y"}]))
    value, _ = run(ProvideList(Counter, specs, nu.Add(1, 2)))
    assert value == 3
    assert [n for kind, n in Counter.events if kind == "setup"] == ["x", "y"]


def test_provide_stream_body_with_computed_config_spans_the_drain():
    seen: list[str] = []

    class Live:
        def __init__(self, name: str) -> None:
            self.name = name

        def setup(self, ctx: Context) -> None:
            seen.append("setup")

        def cleanup(self) -> None:
            seen.append("close")

    tree = nu.Frame(Cfg, Provide(Live, Cfg.kwargs, nu.Iter([1, 2, 3])), kwargs={"name": "s"})
    assert nu.collect(nu.validate(nu.compile(tree)))[0] == [1, 2, 3]
    assert seen == ["setup", "close"]


@pytest.mark.parametrize("runner", ["sync", "async"])
def test_one_bracket_with_config_used_twice_in_one_program(runner: str):
    # T = Provide(...); foo >> T >> smth >> T. One term, two places; its config
    # is evaluated at each, so each place opens with what the tree holds then.
    t = Provide(Counter, Cfg.kwargs, Cfg.runs.set(Cfg.runs + 1))
    program = Cfg.runs.set(0) >> Cfg.kwargs.set(Cfg.first) >> t >> Cfg.kwargs.set(Cfg.second) >> t
    tree = nu.Frame(Cfg, program, first={"name": "a"}, second={"name": "b"})
    run(tree) if runner == "sync" else asyncio.run(arun(tree))
    assert Counter.events == [("setup", "a"), ("close", "a"), ("setup", "b"), ("close", "b")]


def test_provide_one_kwargs_field_comes_from_a_mem_read():
    tree = nu.Frame(
        Cfg, Provide(Counter, {"name": Cfg.first["name"]}, FabricRef(Counter)), first={"name": "f"}
    )
    value, _ = run(tree)
    assert value.name == "f"


async def test_provide_one_kwargs_field_comes_from_a_mem_read_async():
    tree = nu.Frame(
        Cfg, Provide(Counter, {"name": Cfg.first["name"]}, FabricRef(Counter)), first={"name": "f"}
    )
    value, _ = await arun(tree)
    assert value.name == "f"


def test_provide_a_computed_tag_binds_under_its_value():
    tree = Provide(Counter, {"name": "t"}, FabricRef(Counter).exists(), tag=Cfg.first["k"])
    value, _ = run(nu.Frame(Cfg, tree, first={"k": "computed"}))
    # Bound under the computed tag only, so the tagless read does not reach it.
    assert value is False
    assert Counter.events == [("setup", "t"), ("close", "t")]


def test_provide_list_one_spec_field_is_computed():
    specs = [{"name": "plain"}, {"name": nu.Add("com", "puted")}]
    value, _ = run(ProvideList(Counter, specs, nu.Add(1, 2)))
    assert value == 3
    assert [n for kind, n in Counter.events if kind == "setup"] == ["plain", "computed"]


def test_provide_dict_one_spec_field_is_computed():
    tree = nu.Frame(
        Cfg,
        ProvideDict(Counter, {"a": {"name": Cfg.first["name"]}, "b": {"name": "b"}}, nu.Add(1, 2)),
        first={"name": "from-mem"},
    )
    value, _ = run(tree)
    assert value == 3
    assert [n for kind, n in Counter.events if kind == "setup"] == ["from-mem", "b"]


def test_provide_a_term_quoted_in_kwargs_reaches_the_fabric_as_data():
    class Holds:
        def __init__(self, term: object) -> None:
            self.term = term

    held = nu.Add(1, 2)
    value, _ = run(Provide(Holds, {"term": nu.Literal(held)}, FabricRef(Holds)))
    assert value.term is held
