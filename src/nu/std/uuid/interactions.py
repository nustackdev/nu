"""UUID constructor interactions.

Core can't build a ``uuid.UUID``, so the constructors are the new atoms this
module adds. Everything else a UUID does (attribute reads, comparison) reuses
core interactions, so it lives on the Form, not here.

All are ScalarQuery. ``Uuid4Query`` / ``Uuid1Query`` are non-deterministic
(they read randomness / the clock), so they must not be constant-folded -
see the note in ``forms``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "Uuid1Query",
    "Uuid3Query",
    "Uuid4Query",
    "Uuid5Query",
    "UuidFromBytesQuery",
    "UuidFromIntQuery",
    "UuidFromStrQuery",
]


class Uuid4Query(ScalarQuery):
    """A random UUID (version 4): ``uuid.uuid4()``. No children."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            return uuid4()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            return uuid4()

        return athunk


class Uuid1Query(ScalarQuery):
    """A host/time UUID (version 1): ``uuid.uuid1(node?, clock_seq?)``.

    Zero, one (node), or two (node, clock_seq) children.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            args: list[int] = []
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                args.append(cast("int", v))
            return uuid1(*args)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            args: list[int] = []
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                args.append(cast("int", v))
            return uuid1(*args)

        return athunk


class Uuid3Query(ScalarQuery):
    """A name-based MD5 UUID (version 3): ``uuid.uuid3(namespace, name)``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ns_t, name_t = children

        def thunk(rt: Runtime) -> object:
            ns = ns_t(rt)
            if ns is EMPTY or ns is INVALID:
                return INVALID
            name = name_t(rt)
            if name is EMPTY or name is INVALID:
                return INVALID
            return uuid3(cast("UUID", ns), cast("str", name))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ns_t, name_t = children

        async def athunk(rt: Runtime) -> object:
            ns = await ns_t(rt)
            if ns is EMPTY or ns is INVALID:
                return INVALID
            name = await name_t(rt)
            if name is EMPTY or name is INVALID:
                return INVALID
            return uuid3(cast("UUID", ns), cast("str", name))

        return athunk


class Uuid5Query(ScalarQuery):
    """A name-based SHA-1 UUID (version 5): ``uuid.uuid5(namespace, name)``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ns_t, name_t = children

        def thunk(rt: Runtime) -> object:
            ns = ns_t(rt)
            if ns is EMPTY or ns is INVALID:
                return INVALID
            name = name_t(rt)
            if name is EMPTY or name is INVALID:
                return INVALID
            return uuid5(cast("UUID", ns), cast("str", name))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ns_t, name_t = children

        async def athunk(rt: Runtime) -> object:
            ns = await ns_t(rt)
            if ns is EMPTY or ns is INVALID:
                return INVALID
            name = await name_t(rt)
            if name is EMPTY or name is INVALID:
                return INVALID
            return uuid5(cast("UUID", ns), cast("str", name))

        return athunk


class UuidFromStrQuery(ScalarQuery):
    """Parse a hex string into a UUID: ``UUID(value)``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return UUID(str(v))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return UUID(str(v))

        return athunk


class UuidFromBytesQuery(ScalarQuery):
    """Build a UUID from 16 bytes: ``UUID(bytes=value)``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return UUID(bytes=cast("bytes", v))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return UUID(bytes=cast("bytes", v))

        return athunk


class UuidFromIntQuery(ScalarQuery):
    """Build a UUID from a 128-bit integer: ``UUID(int=value)``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return UUID(int=cast("int", v))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return UUID(int=cast("int", v))

        return athunk
