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


class Counter(nu.Fabric):
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
    value, _ = run(Provide(Counter, kwargs={"name": "a"}, body=FabricRef(Counter)))
    assert isinstance(value, Counter)
    assert value.name == "a"


def test_provide_teardown_fires_lifo_on_exit():
    run(Provide(Counter, kwargs={"name": "a"}, body=FabricRef(Counter)))
    assert Counter.events == [("setup", "a"), ("close", "a")]


def test_provide_tag_sugar_binds_under_that_tag():
    class Store(nu.Fabric):
        pass

    bracket = Provide(Store, kwargs={}, body=FabricRef(Store), tag="alpha")
    ctx = Context()
    with bracket._enter(ctx):
        assert ctx.fabrics.has(Store, "alpha")
        assert not ctx.fabrics.has(Store, "beta")


def test_provide_tags_multi_bind_requires_full_tag_set():
    class Store(nu.Fabric):
        pass

    # Multi-tag is AND: the lookup key is the full frozenset of tags.
    # Subset resolution runs the OTHER way (a more-specific request falls
    # back to a less-specific binding), never a less-specific request
    # matching a more-specific binding.
    bracket = Provide(Store, kwargs={}, body=FabricRef(Store), tags=("gpu", "worker"))
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
    class Store(nu.Fabric):
        pass

    bracket = Provide(Store, kwargs={}, body=FabricRef(Store), tag="primary", tags=("gpu",))
    ctx = Context()
    with bracket._enter(ctx):
        inst = ctx.fabrics.get(Store, "primary", "gpu")
        assert inst is not None
        # Order of tags at lookup does not matter (frozenset).
        assert ctx.fabrics.get(Store, "gpu", "primary") is inst


def test_provide_predicate_forwards_to_ctx_bind():
    class Store(nu.Fabric):
        def __init__(self) -> None:
            self.owner = "unset"

    # Inline body reading through a plain Python bracket: build the bracket
    # + open its _open manually to inspect ctx state.
    def match_site(site: int) -> bool:
        return site < 5

    bracket = Provide(Store, kwargs={}, body=FabricRef(Store), predicate=match_site)
    ctx = Context()
    with bracket._enter(ctx):
        # A predicate binding resolves only against data.
        assert not ctx.fabrics.has(Store)  # no data kwargs -> nothing to match
        assert ctx.fabrics.get(Store, site=3) is not None
        with pytest.raises(LookupError):
            ctx.fabrics.get(Store, site=10)


# --- ProvideList ---------------------------------------------------------


def test_provide_list_binds_each_by_index():
    class Store(nu.Fabric):
        def __init__(self, i: int) -> None:
            self.i = i

    bracket = ProvideList(
        Store, specs=[{"i": 0}, {"i": 1}, {"i": 2}], body=FabricRef(Store), base_tag=10
    )
    ctx = Context()
    with bracket._enter(ctx):
        assert ctx.fabrics.get(Store, 10).i == 0
        assert ctx.fabrics.get(Store, 11).i == 1
        assert ctx.fabrics.get(Store, 12).i == 2


def test_provide_list_extra_tags_share_across_fleet():
    class Store(nu.Fabric):
        def __init__(self, i: int) -> None:
            self.i = i

    bracket = ProvideList(
        Store, specs=[{"i": 0}, {"i": 1}], body=FabricRef(Store), extra_tags=("worker",)
    )
    ctx = Context()
    with bracket._enter(ctx):
        # index + shared extra tag both address the same binding.
        assert ctx.fabrics.get(Store, 0, "worker").i == 0
        assert ctx.fabrics.get(Store, 1, "worker").i == 1


def test_provide_list_teardown_is_lifo():
    run(
        ProvideList(
            Counter,
            specs=[{"name": "a"}, {"name": "b"}, {"name": "c"}],
            body=FabricRef(Counter),
        )
    )
    setups = [n for kind, n in Counter.events if kind == "setup"]
    closes = [n for kind, n in Counter.events if kind == "close"]
    assert setups == ["a", "b", "c"]
    assert closes == ["c", "b", "a"]


def test_provide_list_partial_setup_failure_tears_down_completed():
    class Flaky(nu.Fabric):
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
        specs=[{"i": 0}, {"i": 1}, {"i": 2, "boom": True}, {"i": 3}],
        body=FabricRef(Flaky),
    )
    with pytest.raises(RuntimeError, match="boom 2"):
        run(bracket)
    assert Flaky.events == ["setup:0", "setup:1", "close:1", "close:0"]


# --- ProvideDict ---------------------------------------------------------


def test_provide_dict_binds_each_by_key():
    class Store(nu.Fabric):
        def __init__(self, name: str) -> None:
            self.name = name

    bracket = ProvideDict(
        Store,
        specs={"gpu": {"name": "g"}, "cpu": {"name": "c"}},
        body=FabricRef(Store),
    )
    ctx = Context()
    with bracket._enter(ctx):
        assert ctx.fabrics.get(Store, "gpu").name == "g"
        assert ctx.fabrics.get(Store, "cpu").name == "c"


def test_provide_dict_extra_tags_share_across_fleet():
    class Store(nu.Fabric):
        def __init__(self, name: str) -> None:
            self.name = name

    bracket = ProvideDict(
        Store,
        specs={"gpu": {"name": "g"}, "cpu": {"name": "c"}},
        body=FabricRef(Store),
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

    class Member(nu.Fabric):
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
        specs={"fast": {"k": "fast"}, "slow": {"k": "slow"}, "bad": {"k": "bad"}},
        body=FabricRef(Member),
        parallel=True,
    )
    with pytest.raises(RuntimeError, match="bad setup"):
        await arun(bracket)
    assert events == ["setup:fast", "unwound:slow", "close:fast"]


# --- async lifecycle -----------------------------------------------------


async def test_provide_prefers_asetup_when_defined():
    class AsyncStore(nu.Fabric):
        events: ClassVar[list[str]] = []

        def __init__(self) -> None:
            self.name = "x"

        async def asetup(self, ctx: Context) -> None:
            AsyncStore.events.append("asetup")

        async def acleanup(self) -> None:
            AsyncStore.events.append("acleanup")

    value, _ = await arun(Provide(AsyncStore, kwargs={}, body=FabricRef(AsyncStore)))
    assert isinstance(value, AsyncStore)
    assert AsyncStore.events == ["asetup", "acleanup"]


# --- DI through ctx.get in setup -----------------------------------------


def test_inner_provide_reads_outer_binding_via_ctx_get():
    class Codec(nu.Fabric):
        def __init__(self, kind: str) -> None:
            self.kind = kind

    class Storage(nu.Fabric):
        def __init__(self) -> None:
            self.codec_kind: str | None = None

        def setup(self, ctx: Context) -> None:
            self.codec_kind = ctx.fabrics.get(Codec).kind

    app = Provide(
        Codec, kwargs={"kind": "json"}, body=Provide(Storage, kwargs={}, body=FabricRef(Storage))
    )
    value, _ = run(app)
    assert isinstance(value, Storage) and value.codec_kind == "json"


# --- async-only marker, sync fallback, the Fabric base check -------------


def test_provide_refuses_async_only_marker_under_sync_open():
    class AsyncOnly(nu.Fabric):
        async_only = True

        async def asetup(self, ctx: Context) -> None: ...
        async def acleanup(self) -> None: ...

    with pytest.raises(RuntimeError, match="async_only"):
        run(Provide(AsyncOnly, kwargs={}, body=FabricRef(AsyncOnly)))


async def test_provide_async_only_marker_does_not_gate_arun():
    class AsyncOnly(nu.Fabric):
        async_only = True
        events: ClassVar[list[str]] = []

        async def asetup(self, ctx: Context) -> None:
            AsyncOnly.events.append("asetup")

        async def acleanup(self) -> None:
            AsyncOnly.events.append("acleanup")

    AsyncOnly.events.clear()
    await arun(Provide(AsyncOnly, kwargs={}, body=FabricRef(AsyncOnly)))
    assert AsyncOnly.events == ["asetup", "acleanup"]


async def test_provide_async_runner_falls_back_to_sync_lifecycle():
    class SyncOnly(nu.Fabric):
        events: ClassVar[list[str]] = []

        def setup(self, ctx: Context) -> None:
            SyncOnly.events.append("setup")

        def cleanup(self) -> None:
            SyncOnly.events.append("cleanup")

    SyncOnly.events.clear()
    await arun(Provide(SyncOnly, kwargs={}, body=FabricRef(SyncOnly)))
    assert SyncOnly.events == ["setup", "cleanup"]


# --- any class: lifecycle by what the instance is ---------------------------


class Plain:
    """No lifecycle: only bound and unbound."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs


class Managed:
    """A sync context manager that records how it was entered and exited."""

    events: ClassVar[list[object]] = []

    def __enter__(self) -> str:
        Managed.events.append("enter")
        return "not the instance"

    def __exit__(self, kind: object, exc: object, tb: object) -> bool:
        Managed.events.append(("exit", kind))
        return True  # asks to swallow; Provide must not


class AManaged:
    """An async context manager, with a sync half the sync runtime uses."""

    events: ClassVar[list[object]] = []

    def __enter__(self) -> None:
        AManaged.events.append("enter")

    def __exit__(self, *exc: object) -> None:
        AManaged.events.append("exit")

    async def __aenter__(self) -> None:
        AManaged.events.append("aenter")

    async def __aexit__(self, kind: object, exc: object, tb: object) -> None:
        AManaged.events.append(("aexit", kind))


class AsyncOnlyManaged:
    async def __aenter__(self) -> None: ...
    async def __aexit__(self, *exc: object) -> None: ...


@pytest.fixture(autouse=True)
def _reset_managed() -> None:
    Managed.events.clear()
    AManaged.events.clear()


def test_provide_binds_a_plain_class():
    value, _ = run(Provide(Plain, kwargs={"a": 1}, body=FabricRef(Plain)))
    assert isinstance(value, Plain)
    assert value.kwargs == {"a": 1}


def test_provide_binds_a_plain_dict_fresh_each_entry():
    bracket = Provide(dict, kwargs={"n": 1}, body=FabricRef(dict))
    first, _ = run(bracket)
    second, _ = run(bracket)
    assert first == second == {"n": 1}
    assert first is not second


def test_provide_unbinds_a_plain_class_on_exit():
    ctx = Context()
    with Provide(Plain, kwargs={}, body=FabricRef(Plain))._enter(ctx):
        assert ctx.fabrics.has(Plain)
    assert not ctx.fabrics.has(Plain)


def test_provide_feeds_mem_refs_through_bind_as(capsys):
    class Store(dict):
        pass

    body = nu.IntRef("n").set(10) >> nu.print(nu.IntRef("n"))
    run(Provide(Store, kwargs={}, body=body, bind_as=dict))
    assert capsys.readouterr().out == "10\n"


def test_provide_passes_positional_args_before_kwargs():
    value, _ = run(Provide(Plain, kwargs={"k": 3}, body=FabricRef(Plain), args=(1, 2)))
    assert value.args == (1, 2)
    assert value.kwargs == {"k": 3}


def test_provide_takes_computed_positional_args():
    value, _ = run(Provide(Plain, kwargs=None, body=FabricRef(Plain), args=(nu.int(1) + 1,)))
    assert value.args == (2,)


def test_provide_config_names_args():
    assert config(Provide(Plain, kwargs={}, body=FabricRef(Plain), args=(1,)))["args"] == (1,)


def test_provide_enters_and_exits_a_context_manager_binding_the_instance():
    value, _ = run(Provide(Managed, kwargs={}, body=FabricRef(Managed)))
    assert isinstance(value, Managed)
    assert Managed.events == ["enter", ("exit", None)]


def test_provide_hands_the_body_error_to_exit_and_still_raises():
    class Boom(nu.Fabric):
        def setup(self, ctx: Context) -> None:
            raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        run(Provide(Managed, kwargs={}, body=Provide(Boom, kwargs={}, body=FabricRef(Boom))))
    assert Managed.events == ["enter", ("exit", ValueError)]


async def test_provide_uses_the_async_protocol_under_arun():
    await arun(Provide(AManaged, kwargs={}, body=FabricRef(AManaged)))
    assert AManaged.events == ["aenter", ("aexit", None)]


def test_provide_uses_the_sync_protocol_under_run():
    run(Provide(AManaged, kwargs={}, body=FabricRef(AManaged)))
    assert AManaged.events == ["enter", "exit"]


def test_provide_refuses_an_async_only_context_manager_under_run():
    with pytest.raises(RuntimeError, match=r"AsyncOnlyManaged is an async context manager"):
        run(Provide(AsyncOnlyManaged, kwargs={}, body=FabricRef(AsyncOnlyManaged)))


async def test_provide_runs_an_async_only_context_manager_under_arun():
    value, _ = await arun(Provide(AsyncOnlyManaged, kwargs={}, body=FabricRef(AsyncOnlyManaged)))
    assert isinstance(value, AsyncOnlyManaged)


def test_provide_prefers_fabric_hooks_over_the_context_manager():
    class Both(nu.Fabric):
        events: ClassVar[list[str]] = []

        def setup(self, ctx: Context) -> None:
            Both.events.append("setup")

        def cleanup(self) -> None:
            Both.events.append("cleanup")

        def __enter__(self) -> None:
            Both.events.append("enter")

        def __exit__(self, *exc: object) -> None:
            Both.events.append("exit")

    run(Provide(Both, kwargs={}, body=FabricRef(Both)))
    assert Both.events == ["setup", "cleanup"]


def test_provide_tears_down_mixed_lifecycles_in_reverse():
    body = Provide(Counter, kwargs={"name": "inner"}, body=FabricRef(Counter))
    run(Provide(Managed, kwargs={}, body=Provide(Plain, kwargs={}, body=body)))
    assert Counter.events == [("setup", "inner"), ("close", "inner")]
    assert Managed.events == ["enter", ("exit", None)]


def test_provide_list_and_dict_take_any_class():
    fleet = ProvideList(Managed, specs=[{}, {}], body=FabricRef(Managed))
    run(fleet)
    assert Managed.events == ["enter", "enter", ("exit", None), ("exit", None)]
    named = ProvideDict(dict, specs={"a": {"x": 1}, "b": {"x": 2}}, body=FabricRef(dict))
    ctx = Context()
    with named._enter(ctx):
        assert ctx.fabrics.get(dict, "a") == {"x": 1}
        assert ctx.fabrics.get(dict, "b") == {"x": 2}


async def test_provide_dict_parallel_enters_async_context_managers():
    await arun(
        ProvideDict(AManaged, specs={"a": {}, "b": {}}, body=FabricRef(AManaged), parallel=True)
    )
    assert AManaged.events.count("aenter") == 2
    assert AManaged.events.count(("aexit", None)) == 2


def test_provide_refuses_what_is_not_a_class_at_build():
    with pytest.raises(TypeError, match=r"^Provide takes a class, got"):
        Provide(Plain(), kwargs={}, body=FabricRef(Plain))
    with pytest.raises(TypeError, match=r"^ProvideList takes a class"):
        ProvideList(3, specs=[{}], body=FabricRef(Plain))
    with pytest.raises(TypeError, match=r"^ProvideDict takes a class"):
        ProvideDict("Plain", specs={"a": {}}, body=FabricRef(Plain))


async def test_provide_refuses_a_computed_value_that_is_not_a_class_at_open():
    bracket = Provide(nu.Literal(Plain()), kwargs={}, body=FabricRef(Plain))
    with pytest.raises(TypeError, match=r"^Provide takes a class"):
        run(bracket)
    with pytest.raises(TypeError, match=r"^Provide takes a class"):
        await arun(bracket)


def test_fabric_ref_names_any_class():
    class PlainRef(FabricRef):
        fabric = Plain

    assert run(Provide(Plain, kwargs={}, body=PlainRef()))[0].kwargs == {}


def test_fabric_ref_refuses_a_named_value_that_is_not_a_class():
    with pytest.raises(TypeError, match=r"fabric must be a class"):

        class BadRef(FabricRef):
            fabric = Plain()


def test_provide_refuses_an_async_only_setup_under_sync_open():
    class AsyncSetup(nu.Fabric):
        events: ClassVar[list[str]] = []

        def __init__(self) -> None:
            AsyncSetup.events.append("init")

        async def asetup(self, ctx: Context) -> None: ...

    with pytest.raises(RuntimeError, match=r"AsyncSetup has no sync setup; use nu\.arun"):
        run(Provide(AsyncSetup, kwargs={}, body=FabricRef(AsyncSetup)))
    assert AsyncSetup.events == []


def test_provide_refuses_an_async_only_cleanup_under_sync_open():
    class AsyncCleanup(nu.Fabric):
        def setup(self, ctx: Context) -> None: ...
        async def acleanup(self) -> None: ...

    with pytest.raises(RuntimeError, match=r"AsyncCleanup has no sync cleanup; use nu\.arun"):
        run(Provide(AsyncCleanup, kwargs={}, body=FabricRef(AsyncCleanup)))
    with pytest.raises(RuntimeError, match="no sync cleanup"):
        run(ProvideList(AsyncCleanup, specs=[{}], body=FabricRef(AsyncCleanup)))
    with pytest.raises(RuntimeError, match="no sync cleanup"):
        run(ProvideDict(AsyncCleanup, specs={"a": {}}, body=FabricRef(AsyncCleanup)))


def test_provide_runs_a_fabric_with_both_halves_under_sync_open():
    class Both(nu.Fabric):
        events: ClassVar[list[str]] = []

        def setup(self, ctx: Context) -> None:
            Both.events.append("setup")

        async def asetup(self, ctx: Context) -> None:
            Both.events.append("asetup")

    run(Provide(Both, kwargs={}, body=FabricRef(Both)))
    assert Both.events == ["setup"]


async def test_provide_runs_an_async_only_setup_under_arun():
    class AsyncSetup(nu.Fabric):
        events: ClassVar[list[str]] = []

        async def asetup(self, ctx: Context) -> None:
            AsyncSetup.events.append("asetup")

    await arun(Provide(AsyncSetup, kwargs={}, body=FabricRef(AsyncSetup)))
    assert AsyncSetup.events == ["asetup"]


def test_provide_list_refuses_async_only_marker_under_sync_open():
    class AsyncOnly(nu.Fabric):
        async_only = True

        def __init__(self, i: int) -> None:
            self.i = i

        async def asetup(self, ctx: Context) -> None: ...
        async def acleanup(self) -> None: ...

    with pytest.raises(RuntimeError, match="async_only"):
        run(ProvideList(AsyncOnly, specs=[{"i": 0}], body=FabricRef(AsyncOnly)))


def test_provide_dict_refuses_async_only_marker_under_sync_open():
    class AsyncOnly(nu.Fabric):
        async_only = True

        def __init__(self, k: str) -> None:
            self.k = k

        async def asetup(self, ctx: Context) -> None: ...
        async def acleanup(self) -> None: ...

    with pytest.raises(RuntimeError, match="async_only"):
        run(ProvideDict(AsyncOnly, specs={"a": {"k": "a"}}, body=FabricRef(AsyncOnly)))


# --- config is children ----------------------------------------------------


class Cfg(nu.Shape):
    """Mem slots a tree reads a Provide's config from."""

    kwargs = nu.DictRef.slot(nu.StrRef)
    first = nu.DictRef.slot(nu.StrRef)
    second = nu.DictRef.slot(nu.StrRef)
    runs = nu.IntRef.slot()


def test_provide_config_sits_after_the_body_as_children():
    body = FabricRef(Counter)
    bracket = Provide(Counter, kwargs={"name": "a"}, body=body, tag="t")
    head, cls, args, kwargs, tags, predicate, bind_as = nu.tree.children(bracket)
    assert head is body
    assert [c.value for c in (cls, predicate, bind_as)] == [Counter, None, None]
    # kwargs, tags and args are built field by field, each one a child of its own.
    assert [c.value for c in nu.tree.children(kwargs)] == ["a"]
    assert [c.value for c in nu.tree.children(tags)] == ["t"]
    assert nu.tree.children(args) == ()
    assert config(bracket) == {
        "cls": Counter,
        "args": (),
        "kwargs": {"name": "a"},
        "tags": ("t",),
        "predicate": None,
        "bind_as": None,
    }


def test_provide_kwargs_come_from_a_mem_read():
    tree = nu.Frame(
        Cfg,
        Provide(Counter, kwargs=Cfg.kwargs, body=FabricRef(Counter)),
        kwargs={"name": "from-mem"},
    )
    value, _ = run(tree)
    assert value.name == "from-mem"
    assert Counter.events == [("setup", "from-mem"), ("close", "from-mem")]


async def test_provide_kwargs_come_from_a_mem_read_async():
    tree = nu.Frame(
        Cfg,
        Provide(Counter, kwargs=Cfg.kwargs, body=FabricRef(Counter)),
        kwargs={"name": "from-mem"},
    )
    value, _ = await arun(tree)
    assert value.name == "from-mem"


def test_provide_list_specs_come_from_a_computation():
    specs = nu.Collect(nu.Iter([{"name": "x"}, {"name": "y"}]))
    value, _ = run(ProvideList(Counter, specs=specs, body=nu.Add(1, 2)))
    assert value == 3
    assert [n for kind, n in Counter.events if kind == "setup"] == ["x", "y"]


def test_provide_stream_body_with_computed_config_spans_the_drain():
    seen: list[str] = []

    class Live(nu.Fabric):
        def __init__(self, name: str) -> None:
            self.name = name

        def setup(self, ctx: Context) -> None:
            seen.append("setup")

        def cleanup(self) -> None:
            seen.append("close")

    tree = nu.Frame(
        Cfg, Provide(Live, kwargs=Cfg.kwargs, body=nu.Iter([1, 2, 3])), kwargs={"name": "s"}
    )
    assert nu.collect(nu.validate(nu.compile(tree)))[0] == [1, 2, 3]
    assert seen == ["setup", "close"]


@pytest.mark.parametrize("runner", ["sync", "async"])
def test_one_bracket_with_config_used_twice_in_one_program(runner: str):
    # T = Provide(...); foo >> T >> smth >> T. One term, two places; its config
    # is evaluated at each, so each place opens with what the tree holds then.
    t = Provide(Counter, kwargs=Cfg.kwargs, body=Cfg.runs.set(Cfg.runs + 1))
    program = Cfg.runs.set(0) >> Cfg.kwargs.set(Cfg.first) >> t >> Cfg.kwargs.set(Cfg.second) >> t
    tree = nu.Frame(Cfg, program, first={"name": "a"}, second={"name": "b"})
    run(tree) if runner == "sync" else asyncio.run(arun(tree))
    assert Counter.events == [("setup", "a"), ("close", "a"), ("setup", "b"), ("close", "b")]


def test_provide_one_kwargs_field_comes_from_a_mem_read():
    tree = nu.Frame(
        Cfg,
        Provide(Counter, kwargs={"name": Cfg.first["name"]}, body=FabricRef(Counter)),
        first={"name": "f"},
    )
    value, _ = run(tree)
    assert value.name == "f"


async def test_provide_one_kwargs_field_comes_from_a_mem_read_async():
    tree = nu.Frame(
        Cfg,
        Provide(Counter, kwargs={"name": Cfg.first["name"]}, body=FabricRef(Counter)),
        first={"name": "f"},
    )
    value, _ = await arun(tree)
    assert value.name == "f"


def test_provide_a_computed_tag_binds_under_its_value():
    tree = Provide(
        Counter, kwargs={"name": "t"}, body=FabricRef(Counter).exists(), tag=Cfg.first["k"]
    )
    value, _ = run(nu.Frame(Cfg, tree, first={"k": "computed"}))
    # Bound under the computed tag only, so the tagless read does not reach it.
    assert value is False
    assert Counter.events == [("setup", "t"), ("close", "t")]


def test_provide_list_one_spec_field_is_computed():
    specs = [{"name": "plain"}, {"name": nu.Add("com", "puted")}]
    value, _ = run(ProvideList(Counter, specs=specs, body=nu.Add(1, 2)))
    assert value == 3
    assert [n for kind, n in Counter.events if kind == "setup"] == ["plain", "computed"]


def test_provide_dict_one_spec_field_is_computed():
    tree = nu.Frame(
        Cfg,
        ProvideDict(
            Counter, specs={"a": {"name": Cfg.first["name"]}, "b": {"name": "b"}}, body=nu.Add(1, 2)
        ),
        first={"name": "from-mem"},
    )
    value, _ = run(tree)
    assert value == 3
    assert [n for kind, n in Counter.events if kind == "setup"] == ["from-mem", "b"]


def test_provide_a_term_quoted_in_kwargs_reaches_the_fabric_as_data():
    class Holds(nu.Fabric):
        def __init__(self, term: object) -> None:
            self.term = term

    held = nu.Add(1, 2)
    value, _ = run(Provide(Holds, kwargs={"term": nu.Literal(held)}, body=FabricRef(Holds)))
    assert value.term is held


def test_provide_takes_only_the_class_by_position():
    # The old ``Provide(cls, kwargs, body)`` shape fails at build, never silently.
    with pytest.raises(TypeError, match="positional argument"):
        Provide(Counter, {"name": "a"}, FabricRef(Counter))  # type: ignore[misc]
    with pytest.raises(TypeError, match="positional argument"):
        ProvideList(Counter, [{"name": "a"}], FabricRef(Counter))  # type: ignore[misc]
    with pytest.raises(TypeError, match="positional argument"):
        ProvideDict(Counter, {"a": {"name": "a"}}, FabricRef(Counter))  # type: ignore[misc]


def test_provide_defaults_to_no_args_and_no_kwargs():
    value, _ = run(Provide(Plain, body=FabricRef(Plain)))
    assert (value.args, value.kwargs) == ((), {})
