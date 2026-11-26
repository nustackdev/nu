"""Tests for ``With``: N-ary bracket sequencer.

``With(a, b, c, body=X)`` enters each bracket's ``_open`` in order (ctx
accumulates across them), runs X against the final ctx, LIFO teardown on exit.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

import nu
from nu.context import FabricRef, Provide, ProvideDict, ProvideList, With
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


# --- basic composition ---------------------------------------------------


def test_with_stacks_provides_and_yields_body_result():
    class A(nu.Fabric):
        pass

    class B(nu.Fabric):
        pass

    tree = With(Provide(A, kwargs={}), Provide(B, kwargs={}), body=FabricRef(B))
    value, _ = run(tree)
    assert isinstance(value, B)


def test_with_no_brackets_just_runs_body():
    class Store(nu.Fabric):
        pass

    tree = With(Provide(Store, kwargs={}), body=FabricRef(Store))
    value, _ = run(tree)
    assert isinstance(value, Store)

    # Zero brackets is legal too: With(body=X) == running X directly.
    tree = Provide(Store, kwargs={}, body=With(body=FabricRef(Store)))
    value, _ = run(tree)
    assert isinstance(value, Store)


def test_with_teardown_is_lifo():
    tree = With(
        Provide(Counter, kwargs={"name": "a"}),
        Provide(Counter, kwargs={"name": "b"}),
        Provide(Counter, kwargs={"name": "c"}),
        body=FabricRef(Counter),
    )
    run(tree)
    setups = [n for kind, n in Counter.events if kind == "setup"]
    closes = [n for kind, n in Counter.events if kind == "close"]
    assert setups == ["a", "b", "c"]
    assert closes == ["c", "b", "a"]


def test_with_ctx_accumulates_inner_reads_outer_via_ctx_get():
    """A later bracket's setup can read an earlier bracket's binding."""

    class Codec(nu.Fabric):
        def __init__(self, kind: str) -> None:
            self.kind = kind

    class Storage(nu.Fabric):
        def __init__(self) -> None:
            self.codec_kind: str | None = None

        def setup(self, ctx: Context) -> None:
            self.codec_kind = ctx.get(Codec).kind

    tree = With(
        Provide(Codec, kwargs={"kind": "binary"}),
        Provide(Storage, kwargs={}),
        body=FabricRef(Storage),
    )
    storage, _ = run(tree)
    assert storage.codec_kind == "binary"


def test_with_composes_provide_provide_list_provide_dict():
    class A(nu.Fabric):
        pass

    class B(nu.Fabric):
        def __init__(self, i: int) -> None:
            self.i = i

    class C(nu.Fabric):
        def __init__(self, k: str) -> None:
            self.k = k

    tree = With(
        Provide(A, kwargs={}),
        ProvideList(B, specs=[{"i": 0}, {"i": 1}]),
        ProvideDict(C, specs={"x": {"k": "x"}, "y": {"k": "y"}}),
        body=FabricRef(A),
    )
    a, _ = run(tree)
    assert isinstance(a, A)


# --- failure semantics ---------------------------------------------------


def test_with_partial_setup_failure_tears_down_already_entered():
    class Flaky(nu.Fabric):
        events: ClassVar[list[str]] = []

        def __init__(self, name: str, boom: bool = False) -> None:
            self.name = name
            self.boom = boom

        def setup(self, ctx: Context) -> None:
            if self.boom:
                raise RuntimeError(f"boom {self.name}")
            Flaky.events.append(f"setup:{self.name}")

        def cleanup(self) -> None:
            Flaky.events.append(f"close:{self.name}")

    tree = With(
        Provide(Flaky, kwargs={"name": "a"}),
        Provide(Flaky, kwargs={"name": "b"}),
        Provide(Flaky, kwargs={"name": "c", "boom": True}),
        Provide(Flaky, kwargs={"name": "d"}),
        body=FabricRef(Flaky),
    )
    with pytest.raises(RuntimeError, match="boom c"):
        run(tree)
    assert Flaky.events == ["setup:a", "setup:b", "close:b", "close:a"]


# --- tags flow through -----------------------------------------------------


def test_with_preserves_bracket_tags():
    class Store(nu.Fabric):
        def __init__(self, name: str) -> None:
            self.name = name

    tree = With(
        Provide(Store, kwargs={"name": "primary"}),
        Provide(Store, kwargs={"name": "cache"}, tag="cache"),
        body=FabricRef(Store),
    )
    # default binding (last bracket wins for untagged? no -- default has no tag,
    # cache has tag="cache", both coexist)
    default, _ = run(tree)
    assert default.name == "primary"

    # Inspect the ctx directly to verify both bindings live.
    bracket = With(
        Provide(Store, kwargs={"name": "primary"}),
        Provide(Store, kwargs={"name": "cache"}, tag="cache"),
    )
    ctx = Context()
    with bracket._enter(ctx) as inner:
        assert inner.get(Store).name == "primary"
        assert inner.get(Store, "cache").name == "cache"


# --- async lifecycle -----------------------------------------------------


async def test_with_async_prefers_asetup_lifo_acleanup():
    class Async(nu.Fabric):
        events: ClassVar[list[str]] = []

        def __init__(self, name: str) -> None:
            self.name = name

        async def asetup(self, ctx: Context) -> None:
            Async.events.append(f"asetup:{self.name}")

        async def acleanup(self) -> None:
            Async.events.append(f"aclose:{self.name}")

    tree = With(
        Provide(Async, kwargs={"name": "a"}),
        Provide(Async, kwargs={"name": "b"}),
        Provide(Async, kwargs={"name": "c"}),
        body=FabricRef(Async),
    )
    await arun(tree)
    setups = [n[7:] for n in Async.events if n.startswith("asetup:")]
    closes = [n[7:] for n in Async.events if n.startswith("aclose:")]
    assert setups == ["a", "b", "c"]
    assert closes == ["c", "b", "a"]


# --- brackets are children -------------------------------------------------


def test_with_brackets_are_real_nodes_of_the_tree():
    a = Provide(Counter, kwargs={"name": "a"})
    b = Provide(Counter, kwargs={"name": "b"})
    body = FabricRef(Counter)
    tree = With(a, b, body=body)

    outer, inner = tree.brackets
    assert nu.tree.children(tree)[0] is outer
    assert nu.tree.children(outer)[0] is inner
    assert nu.tree.children(inner)[0] is body
    assert len(nu.tree.find(tree, lambda n: isinstance(n, Provide))) == 2
    # The brackets given are specs: the cascade holds variants, they keep their own body slot.
    assert outer is not a
    assert isinstance(nu.tree.children(a)[0], nu.Literal)
    assert nu.tree.children(outer)[1:] == nu.tree.children(a)[1:]


def test_with_nests_inside_with_in_order():
    tree = With(
        With(Provide(Counter, kwargs={"name": "a"}), Provide(Counter, kwargs={"name": "b"})),
        Provide(Counter, kwargs={"name": "c"}),
        body=FabricRef(Counter),
    )
    value, _ = run(tree)
    assert value.name == "c"  # the innermost untagged binding shadows the outer ones
    assert Counter.events == [
        ("setup", "a"),
        ("setup", "b"),
        ("setup", "c"),
        ("close", "c"),
        ("close", "b"),
        ("close", "a"),
    ]


def test_with_bracket_config_reads_the_tree():
    class Cfg(nu.Shape):
        kwargs = nu.DictRef.slot(nu.StrRef)

    tree = nu.let(
        Cfg,
        With(Provide(Counter, kwargs=Cfg.kwargs), body=FabricRef(Counter)),
        kwargs={"name": "from-mem"},
    )
    value, _ = run(tree)
    assert value.name == "from-mem"
    assert nu.tree.reads(tree)


def test_with_enter_opens_every_layer_outside_a_tree():
    spec = With(
        With(Provide(Counter, kwargs={"name": "a"})),
        Provide(Counter, kwargs={"name": "b"}, tag="b"),
    )
    ctx = Context()
    with spec._enter(ctx) as inner:
        assert inner.get(Counter).name == "a"
        assert inner.get(Counter, "b").name == "b"
    assert Counter.events == [("setup", "a"), ("setup", "b"), ("close", "b"), ("close", "a")]
