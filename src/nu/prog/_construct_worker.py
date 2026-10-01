"""Child-side of a :class:`~nu.prog.constructors.Venv` brace.

Run as ``python -m nu.prog._construct_worker`` by a *foreign* interpreter -
one with its own ``nu`` install. It reads request frames from stdin, calls
:func:`nu.prog.source.construct`, and writes response frames to stdout. One
request at a time, no interleave: construction is a short CPU-bound call and
a brace is not a throughput device.

Nothing is ever *run* here. The child builds a Nu term and hands it back;
driving that term is the parent's job.

**stdout is the wire.** A snippet is arbitrary python and arbitrary python
prints. If a ``print`` landed on stdout it would appear mid-frame and desync
the parent for good. So the first thing ``main`` does, before any request is
read and long before exec'ing any snippet, is ``os.dup`` the real stdout to a
private fd and repoint fd 1 at stderr. From then on ``print``, a chatty
import, and a C extension writing to fd 1 all land on stderr where they are
visible to a human and harmless to the protocol.

``python -m`` imports the ``nu`` package before this module runs, so that
import happens before the claim and cannot be redirected by it. It is safe
because importing ``nu`` writes nothing to stdout, and it has to stay that
way: the parent treats any byte before the ``ready`` frame as a frame
header.

Wire format: 4-byte big-endian length prefix, then a ``nu.lang.wire``
(cloudpickle) payload.
Frames::

    ('construct', source, entry, scope, filename)   parent -> worker
    ('stop',)                                       parent -> worker
    ('ready',)                                      worker -> parent (once, at start)
    ('ok', term)                                    worker -> parent
    ('diag', diagnostic)                            worker -> parent

The ``ready`` frame exists so a parent can tell "this venv has no usable
``nu``" from "this snippet is slow". A worker that cannot import ``nu``, or
has no ``nu.prog`` to run, never sends it and exits non-zero; the parent sees
EOF instead of hanging.
"""

from __future__ import annotations

import os
import struct
import sys
from typing import TYPE_CHECKING, BinaryIO


if TYPE_CHECKING:
    from collections.abc import Mapping


__all__ = ["main"]


_HEADER = struct.Struct(">I")


def _send(stream: BinaryIO, frame: object) -> None:
    """Write one length-prefixed wire frame and flush it."""
    from nu.lang import wire

    payload = wire.dumps(frame)
    stream.write(_HEADER.pack(len(payload)))
    stream.write(payload)
    stream.flush()


def _recv(stream: BinaryIO) -> object | None:
    """Read one frame, or ``None`` at a clean end of stream."""
    from nu.lang import wire

    header = _read_exactly(stream, _HEADER.size)
    if header is None:
        return None
    (size,) = _HEADER.unpack(header)
    body = _read_exactly(stream, size)
    if body is None:
        return None
    return wire.loads(body)


def _read_exactly(stream: BinaryIO, size: int) -> bytes | None:
    """Read exactly ``size`` bytes; ``None`` if the stream ends first.

    A pipe read is free to return short, so this loops rather than trusting
    one ``read`` to fill the buffer.
    """
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _claim_stdout() -> BinaryIO:
    """Take the real stdout for the wire and point fd 1 at stderr.

    Returns the private duplicate to write frames on. After this call
    nothing the snippet does can reach the parent's read end: ``sys.stdout``,
    ``sys.__stdout__`` and fd 1 itself all go to stderr.
    """
    wire_fd = os.dup(1)
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    sys.__stdout__ = sys.stderr  # type: ignore[misc]
    return os.fdopen(wire_fd, "wb")


def _handle(frame: tuple) -> tuple:
    """Turn one ``construct`` request into its response frame."""
    from nu.prog.diagnostics import Diagnostic
    from nu.prog.source import construct

    _, source, entry, scope, filename = frame
    scope_map: Mapping[str, object] | None = scope
    result = construct(source, entry=entry, scope=scope_map, filename=filename)
    if isinstance(result, Diagnostic):
        return ("diag", result)
    return ("ok", result)


def main() -> int:
    """Claim the wire, announce readiness, then serve until EOF or stop."""
    wire = _claim_stdout()
    inbox = sys.stdin.buffer

    # Import before the ready frame on purpose: an unusable ``nu`` in this
    # venv is a *parent* problem, and the parent detects it as a missing
    # handshake rather than as a failure of some later snippet.
    import nu.prog.source  # noqa: F401

    _send(wire, ("ready",))

    while True:
        frame = _recv(inbox)
        if frame is None:
            return 0
        if not isinstance(frame, tuple) or not frame:
            return 0
        if frame[0] == "stop":
            return 0
        _send(wire, _handle(frame))


if __name__ == "__main__":
    raise SystemExit(main())
