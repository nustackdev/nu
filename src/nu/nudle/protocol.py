"""Wire protocol between a nudle server and a nudle browser tab.

See projects/nu/stack/nudle/protocol.md in the Go space for the spec.

Frame can be built two ways:
- `Frame("mount", ref="", payload=...)` for lifecycle ops (op is a string)
- `Frame(interaction_instance, ref=path, payload=v)` for interactions; the
  op name is the lowercased class name of the interaction. Interactions
  don't declare their own op; the wire name follows the class.
"""

from __future__ import annotations

from typing import Any

import msgpack
from nu.lang.sentinels import is_sentinel


__all__ = [
    "OP_ERROR",
    "OP_MOUNT",
    "OP_NOTIFY",
    "OP_READ",
    "OP_UNMOUNT",
    "Frame",
    "decode",
    "encode",
]


OP_MOUNT = "mount"
OP_UNMOUNT = "unmount"
OP_ERROR = "error"
OP_NOTIFY = "notify"
OP_READ = "read"


def _op_of(op_or_interaction: object) -> str:
    if isinstance(op_or_interaction, str):
        return op_or_interaction
    return type(op_or_interaction).__name__.lower()


class Frame:
    """One wire envelope. Same shape both directions."""

    __slots__ = ("id", "op", "payload", "ref")

    def __init__(
        self,
        op: object,
        *,
        ref: str = "",
        payload: Any = None,
        id: str | None = None,
    ) -> None:
        self.op = _op_of(op)
        self.ref = ref
        self.payload = payload
        self.id = id

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"op": self.op, "ref": self.ref, "payload": self.payload}
        if self.id is not None:
            d["id"] = self.id
        return d

    def __repr__(self) -> str:
        return f"Frame(op={self.op!r}, ref={self.ref!r}, payload={self.payload!r}, id={self.id!r})"


def _msgpack_default(obj: object) -> Any:
    """Coerce values msgpack can't pack on its own.

    Nu sentinels (EMPTY / INVALID) are first-class values: a Ref resolves to
    one when its address is absent or an operation didn't apply. The wire
    carries Nu values, so the display layer maps them to msgpack nil (which
    decodes to None / null on the browser) rather than crashing the
    connection. The browser decides what nil looks like per Ref type (a
    blank cell, a gap in a chart).
    """
    if is_sentinel(obj):
        return None
    raise TypeError(f"Object of type {obj.__class__.__name__} is not msgpack serializable")


def encode(frame: Frame) -> bytes:
    return msgpack.packb(frame.to_dict(), default=_msgpack_default, use_bin_type=True)


def decode(raw: bytes) -> Frame:
    d = msgpack.unpackb(raw, raw=False)
    return Frame(
        d["op"],
        ref=d.get("ref", ""),
        payload=d.get("payload"),
        id=d.get("id"),
    )
