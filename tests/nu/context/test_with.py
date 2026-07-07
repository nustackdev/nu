"""Tests for ``With``: N-ary bracket sequencer.

``With(a, b, c, body=X)`` enters each bracket's ``_open`` in order (ctx
accumulates across them), runs X against the final ctx, LIFO teardown on exit.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from nu.context import FabricRef, Provide, ProvideDict, ProvideList, With
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


# --- basic composition ---------------------------------------------------


def test_with_stacks_provides_and_yields_body_result():
    class A:
        pass

    class B:
        pass

    tree = With(Provide(A, {}), Provide(B, {}), body=FabricRef(B))
    value, _ = run(tree)
    assert isinstance(value, B)


def test_with_no_brackets_just_runs_body():
    class Store:
        pass

    tree = With(Provide(Store, {}), body=FabricRef(Store))
    value, _ = run(tree)
    assert isinstance(value, Store)

    # Zero brackets is legal too: With(body=X) == running X directly.
    tree = Provide(Store, {}, With(body=FabricRef(Store)))
    value, _ = run(tree)
    assert isinstance(value, Store)


def test_with_teardown_is_lifo():
    tree = With(
        Provide(Counter, {"name": "a"}),
        Provide(Counter, {"name": "b"}),
        Provide(Counter, {"name": "c"}),
        body=FabricRef(Counter),
    )
    run(tree)
    setups = [n for kind, n in Counter.events if kind == "setup"]
    closes = [n for kind, n in Counter.events if kind == "close"]
    assert setups == ["a", "b", "c"]
    assert closes == ["c", "b", "a"]


def test_with_ctx_accumulates_inner_reads_outer_via_ctx_get():
    """A later bracket's setup can read an earlier bracket's binding."""

    class Codec:
        def __init__(self, kind: str) -> None:
            self.kind = kind

    class Storage:
        def __init__(self) -> None:
            self.codec_kind: str | None = None

        def setup(self, ctx: Context) -> None:
            self.codec_kind = ctx.get(Codec).kind

    tree = With(
        Provide(Codec, {"kind": "binary"}),
        Provide(Storage, {}),
        body=FabricRef(Storage),
    )
    storage, _ = run(tree)
    assert storage.codec_kind == "binary"


def test_with_composes_provide_provide_list_provide_dict():
    class A:
        pass

    class B:
        def __init__(self, i: int) -> None:
            self.i = i

    class C:
        def __init__(self, k: str) -> None:
            self.k = k

    tree = With(
        Provide(A, {}),
        ProvideList(B, [{"i": 0}, {"i": 1}]),
        ProvideDict(C, {"x": {"k": "x"}, "y": {"k": "y"}}),
        body=FabricRef(A),
    )
    a, _ = run(tree)
    assert isinstance(a, A)


# --- failure semantics ---------------------------------------------------


def test_with_partial_setup_failure_tears_down_already_entered():
    class Flaky:
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
        Provide(Flaky, {"name": "a"}),
        Provide(Flaky, {"name": "b"}),
        Provide(Flaky, {"name": "c", "boom": True}),
        Provide(Flaky, {"name": "d"}),
        body=FabricRef(Flaky),
    )
    with pytest.raises(RuntimeError, match="boom c"):
        run(tree)
    assert Flaky.events == ["setup:a", "setup:b", "close:b", "close:a"]


# --- tags flow through -----------------------------------------------------


def test_with_preserves_bracket_tags():
    class Store:
        def __init__(self, name: str) -> None:
            self.name = name

    tree = With(
        Provide(Store, {"name": "primary"}),
        Provide(Store, {"name": "cache"}, tag="cache"),
        body=FabricRef(Store),
    )
    # default binding (last bracket wins for untagged? no -- default has no tag,
    # cache has tag="cache", both coexist)
    default, _ = run(tree)
    assert default.name == "primary"

    # Inspect the ctx directly to verify both bindings live.
    bracket = With(
        Provide(Store, {"name": "primary"}),
        Provide(Store, {"name": "cache"}, tag="cache"),
    )
    with bracket._open(Context()) as ctx:
        assert ctx.get(Store).name == "primary"
        assert ctx.get(Store, "cache").name == "cache"


# --- async lifecycle -----------------------------------------------------


async def test_with_async_prefers_asetup_lifo_acleanup():
    class Async:
        events: ClassVar[list[str]] = []

        def __init__(self, name: str) -> None:
            self.name = name

        async def asetup(self, ctx: Context) -> None:
            Async.events.append(f"asetup:{self.name}")

        async def acleanup(self) -> None:
            Async.events.append(f"aclose:{self.name}")

    tree = With(
        Provide(Async, {"name": "a"}),
        Provide(Async, {"name": "b"}),
        Provide(Async, {"name": "c"}),
        body=FabricRef(Async),
    )
    await arun(tree)
    setups = [n[7:] for n in Async.events if n.startswith("asetup:")]
    closes = [n[7:] for n in Async.events if n.startswith("aclose:")]
    assert setups == ["a", "b", "c"]
    assert closes == ["c", "b", "a"]
