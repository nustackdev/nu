"""Unit tests for ``nu.lang.runtime.context.fabrics``.

Covers the scoped half of ``Fabrics``: ``bind`` / ``lazy`` provide for the
``with`` body, shadow an outer binding of the same key, and restore it on a
clean exit, on an error, and when a generator holding the scope is exhausted
or closed. Resolution itself is covered in ``test_context.py``.
"""

from __future__ import annotations

import asyncio

import pytest

from nu.lang.runtime import Fabrics


class Storage:
    """Marker service type."""


class Market:
    """Marker scope tag."""


# --- surface --------------------------------------------------------------


def test_the_tables_are_private() -> None:
    public = {n for n in dir(Fabrics) if not n.startswith("_")}
    assert public == {"bind", "get", "has", "lazy", "predicates", "was_opened"}


# --- bind -----------------------------------------------------------------


def test_bind_provides_for_the_scope_only() -> None:
    fabrics = Fabrics()
    with fabrics.bind(Storage, "v"):
        assert fabrics.get(Storage) == "v"
    assert fabrics.has(Storage) is False


def test_bind_shadows_and_restores_the_outer_binding() -> None:
    fabrics = Fabrics()
    with fabrics.bind(Storage, "outer"):
        with fabrics.bind(Storage, "inner"):
            assert fabrics.get(Storage) == "inner"
        assert fabrics.get(Storage) == "outer"
    assert fabrics.has(Storage) is False


def test_bind_restores_on_error() -> None:
    fabrics = Fabrics()
    with fabrics.bind(Storage, "outer"):
        with pytest.raises(ValueError, match="boom"), fabrics.bind(Storage, "inner"):
            raise ValueError("boom")
        assert fabrics.get(Storage) == "outer"


def test_bind_under_a_tag_leaves_the_untagged_binding_alone() -> None:
    fabrics = Fabrics()
    with fabrics.bind(Storage, "plain"):
        with fabrics.bind(Storage, "tagged", Market):
            assert fabrics.get(Storage, Market) == "tagged"
            assert fabrics.get(Storage) == "plain"
        assert fabrics.get(Storage, Market) == "plain"  # falls back again


def test_guarded_bind_is_removed_on_exit() -> None:
    fabrics = Fabrics()
    with fabrics.bind(Storage, "low", gate=lambda n: n < 10):
        assert fabrics.get(Storage, n=5) == "low"
        assert len(fabrics.predicates(Storage)) == 1
    assert fabrics.predicates(Storage) == []
    with pytest.raises(LookupError):
        fabrics.get(Storage, n=5)


def test_bind_held_by_a_generator_lives_across_its_yields() -> None:
    fabrics = Fabrics()

    def stream():
        with fabrics.bind(Storage, "held"):
            yield fabrics.get(Storage)
            yield fabrics.get(Storage)

    gen = stream()
    assert next(gen) == "held"
    assert fabrics.get(Storage) == "held"  # alive between pulls
    gen.close()
    assert fabrics.has(Storage) is False  # released on close


def test_bind_held_by_a_generator_releases_on_exhaustion() -> None:
    fabrics = Fabrics()

    def stream():
        with fabrics.bind(Storage, "held"):
            yield from (1, 2)

    with fabrics.bind(Storage, "outer"):
        assert list(stream()) == [1, 2]
        assert fabrics.get(Storage) == "outer"


async def test_bind_held_by_an_async_generator_releases_on_close() -> None:
    fabrics = Fabrics()

    async def stream():
        with fabrics.bind(Storage, "inner"):
            yield 1
            await asyncio.sleep(0)
            yield 2

    with fabrics.bind(Storage, "outer"):
        agen = stream()
        assert await agen.__anext__() == 1
        assert fabrics.get(Storage) == "inner"
        await agen.aclose()
        assert fabrics.get(Storage) == "outer"


# --- lazy -----------------------------------------------------------------


def test_lazy_builds_on_first_access_and_caches() -> None:
    calls: list[int] = []

    def factory() -> str:
        calls.append(1)
        return "made"

    fabrics = Fabrics()
    with fabrics.lazy(Storage, factory):
        assert fabrics.was_opened(Storage) is False
        assert calls == []
        assert fabrics.get(Storage) == "made"
        assert fabrics.get(Storage) == "made"
        assert fabrics.was_opened(Storage) is True
        assert calls == [1]
    assert fabrics.has(Storage) is False


def test_lazy_never_touched_never_builds() -> None:
    calls: list[int] = []
    fabrics = Fabrics()
    with fabrics.lazy(Storage, lambda: calls.append(1)):
        pass
    assert calls == []


def test_lazy_shadows_and_restores() -> None:
    fabrics = Fabrics()
    with fabrics.bind(Storage, "outer"):
        with fabrics.lazy(Storage, lambda: "inner"):
            assert fabrics.get(Storage) == "inner"
        assert fabrics.get(Storage) == "outer"
        assert fabrics.was_opened(Storage) is False  # the eager outer is back
