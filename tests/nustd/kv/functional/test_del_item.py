"""``del_item`` answers the same on every dict layout, with ``missing_ok`` to opt out.

The op forwards to the view's own ``del``, so every layout:

- deletes a key that is there,
- raises KeyError for one that is not, a never-written container included,
- does nothing for a missing key under ``missing_ok=True``, and leaves a
  never-written container absent.
"""

from __future__ import annotations

import asyncio

import pytest

from nu import Shape, arun, run
from nustd.kv import DictRef, Kh57Ref, OrderedDictRef
from virtuals.views import (
    FlatDictView,
    IndexedDictView,
    LightDictView,
    LogIndexedDictView,
)


class Board(Shape):
    plain = DictRef.slot(int)
    ordered = OrderedDictRef.slot(int)
    logged = DictRef.slot(int, view=LogIndexedDictView)
    indexed = DictRef.slot(int, view=IndexedDictView)
    flat = DictRef.slot(int, view=FlatDictView)
    light = DictRef.slot(int, view=LightDictView)
    sampled = Kh57Ref.slot(int)


LAYOUTS = {
    "dict": (Board.plain, "a", "z"),
    "ordered": (Board.ordered, "a", "z"),
    "log_indexed": (Board.logged, "a", "z"),
    "indexed": (Board.indexed, "a", "z"),
    "flat": (Board.flat, "a", "z"),
    "light": (Board.light, "a", "z"),
    "kh57": (Board.sampled, 1, 9),
}


@pytest.fixture(params=LAYOUTS)
def layout(request):
    return LAYOUTS[request.param]


def test_a_present_key_is_deleted(ctx, layout) -> None:
    ref, key, _ = layout
    run(ref.set_item(key, 1), ctx)
    run(ref.del_item(key), ctx)
    assert run(ref.contains(key), ctx)[0] is False


def test_a_missing_key_raises(ctx, layout) -> None:
    ref, key, missing = layout
    run(ref.set_item(key, 1), ctx)
    with pytest.raises(KeyError):
        run(ref.del_item(missing), ctx)
    assert run(ref.contains(key), ctx)[0] is True


def test_a_never_written_container_holds_no_key(ctx, layout) -> None:
    ref, _, missing = layout
    with pytest.raises(KeyError):
        run(ref.del_item(missing), ctx)


def test_missing_ok_skips_a_missing_key(ctx, layout) -> None:
    ref, key, missing = layout
    run(ref.set_item(key, 1), ctx)
    run(ref.del_item(missing, missing_ok=True), ctx)
    assert run(ref.contains(key), ctx)[0] is True


def test_missing_ok_deletes_a_present_key(ctx, layout) -> None:
    ref, key, _ = layout
    run(ref.set_item(key, 1), ctx)
    run(ref.del_item(key, missing_ok=True), ctx)
    assert run(ref.contains(key), ctx)[0] is False


def test_missing_ok_leaves_a_never_written_container_absent(ctx, layout) -> None:
    ref, _, missing = layout
    run(ref.del_item(missing, missing_ok=True), ctx)
    assert run(ref.exists(), ctx)[0] is False


def test_the_async_path_answers_the_same(ctx, layout) -> None:
    ref, key, missing = layout

    async def go() -> None:
        await arun(ref.set_item(key, 1), ctx)
        await arun(ref.del_item(missing, missing_ok=True), ctx)
        with pytest.raises(KeyError):
            await arun(ref.del_item(missing), ctx)
        await arun(ref.del_item(key), ctx)

    asyncio.run(go())
    assert run(ref.contains(key), ctx)[0] is False
