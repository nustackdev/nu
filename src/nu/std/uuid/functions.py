"""Module-level functions for ``nu.std.uuid`` - the function namespace.

These mirror ``uuid.uuid1`` / ``uuid.uuid3`` / ``uuid.uuid4`` / ``uuid.uuid5``:
free functions, not methods on the type. Each is a thin wrapper that builds its
constructor interaction atom and returns a ``UUID`` form. The atoms live in
``interactions``; the value type lives in ``forms``.

``uuid4`` / ``uuid1`` are non-deterministic (randomness / the clock), so their
atoms must not be constant-folded - open item until the model grows a purity tag.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.std.uuid.forms import UUID


if TYPE_CHECKING:
    from nu.lang import IntArg, StrArg
    from nu.std.uuid.forms import UUIDArg


__all__ = ["uuid1", "uuid3", "uuid4", "uuid5"]


def uuid4() -> UUID:
    """A random UUID (version 4): mirrors ``uuid.uuid4()``."""
    from nu.std.uuid.interactions import Uuid4Query

    return UUID(Uuid4Query())


def uuid1(node: IntArg | None = None, clock_seq: IntArg | None = None) -> UUID:
    """A host/time UUID (version 1): mirrors ``uuid.uuid1()``."""
    from nu.std.uuid.interactions import Uuid1Query

    if node is not None and clock_seq is not None:
        return UUID(Uuid1Query(node, clock_seq))
    if node is not None:
        return UUID(Uuid1Query(node))
    return UUID(Uuid1Query())


def uuid3(namespace: UUIDArg, name: StrArg) -> UUID:
    """A name-based MD5 UUID (version 3): mirrors ``uuid.uuid3()``."""
    from nu.std.uuid.interactions import Uuid3Query

    return UUID(Uuid3Query(namespace, name))


def uuid5(namespace: UUIDArg, name: StrArg) -> UUID:
    """A name-based SHA-1 UUID (version 5): mirrors ``uuid.uuid5()``."""
    from nu.std.uuid.interactions import Uuid5Query

    return UUID(Uuid5Query(namespace, name))
