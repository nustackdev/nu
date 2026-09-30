"""What Nu sends to another process or stores as bytes, it writes with cloudpickle.

A tree crossing a process boundary may hold what plain pickle refuses: a class
defined inside a function, a lambda, the anonymous Shape a ``nu.let``
makes. cloudpickle writes those by value and anything importable by reference,
and reads them back. This module is that one rule, both directions through
cloudpickle. Every transport in the stack goes through it, never through
``pickle.dumps`` or a ``multiprocessing`` connection's own ``send`` /
``recv``, which pickle implicitly with plain pickle.

Both ends of every wire here are trusted: a parent and the child it spawned.
Loading pickle data from anyone else runs their code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import cloudpickle


if TYPE_CHECKING:
    from multiprocessing.connection import Connection


__all__ = ["dumps", "loads", "recv", "send"]


def dumps(obj: object) -> bytes:
    """``obj`` as pickle bytes, with the unimportable parts written by value."""
    data: bytes = cloudpickle.dumps(obj)
    return data


def loads(data: bytes) -> Any:  # noqa: ANN401 -- unpickled data has no static type
    """The object ``data`` holds, from a trusted peer."""
    return cloudpickle.loads(data)


def send(conn: Connection, obj: object) -> None:
    """Send ``obj`` down a ``multiprocessing`` connection as cloudpickle bytes."""
    conn.send_bytes(dumps(obj))


def recv(conn: Connection) -> Any:  # noqa: ANN401 -- unpickled data has no static type
    """Receive one object sent with :func:`send`."""
    return loads(conn.recv_bytes())
