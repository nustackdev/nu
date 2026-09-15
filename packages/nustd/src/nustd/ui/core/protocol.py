"""Wire protocol between a nustd.ui server and a browser tab.

See projects/nu/stack/nudle/protocol.md in the Go space for the spec.

Frame can be built two ways:
- `Frame("init", ref=path, chain=...)` for lifecycle ops (op is a string)
- `Frame(interaction_instance, ref=path, payload=v)` for interactions; the
  op name is the lowercased class name of the interaction. Interactions
  don't declare their own op; the wire name follows the class.

`ref` is a path: the Ref chain's segments, root-first, shipped as an array.
It stays a sequence end to end -- a segment may hold any character, dots
included, so there is no separator that could take it apart again.

`chain` is that same path annotated: one `(segment, type, props)` triple per
level, root-first, so the browser can create every node on the way down the
first time it sees a write. Every write ships the whole chain even when the
nodes already exist -- the sender is stateless and the browser heals itself.

Wire format is transport-agnostic -- ships bytes; hosts (nudle, others)
choose the concrete channel (ws, sse, etc).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import msgpack

from nu.lang.sentinels import is_sentinel


if TYPE_CHECKING:
    from collections.abc import Sequence


__all__ = [
    "OP_ERROR",
    "OP_INIT",
    "OP_NOTIFY",
    "OP_READ",
    "OP_REMOVE",
    "OP_WRITE",
    "Frame",
    "decode",
    "encode",
]


OP_ERROR = "error"
OP_NOTIFY = "notify"
OP_READ = "read"
OP_WRITE = "write"
OP_REMOVE = "remove"
# Chain, no payload: brings a node into being ahead of the first write to
# it. A boot batch is a run of these.
OP_INIT = "init"


def _op_of(op_or_interaction: object) -> str:
    if isinstance(op_or_interaction, str):
        return op_or_interaction
    return type(op_or_interaction).__name__.lower()


class Frame:
    """One wire envelope. Same shape both directions."""

    __slots__ = ("chain", "id", "op", "payload", "ref")

    def __init__(
        self,
        op: object,
        *,
        ref: Sequence[str] = (),
        payload: Any = None,
        id: str | None = None,
        chain: Sequence[tuple[str, str, dict[str, Any]]] = (),
    ) -> None:
        self.op = _op_of(op)
        self.ref = tuple(ref)
        self.payload = payload
        self.id = id
        self.chain = tuple((seg, typ, props) for seg, typ, props in chain)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"op": self.op, "ref": list(self.ref), "payload": self.payload}
        if self.id is not None:
            d["id"] = self.id
        # Omitted when empty so frames that carry no chain stay exactly what
        # they were before the field existed.
        if self.chain:
            d["chain"] = [[seg, typ, props] for seg, typ, props in self.chain]
        return d

    def __repr__(self) -> str:
        return (
            f"Frame(op={self.op!r}, ref={self.ref!r}, payload={self.payload!r}, "
            f"id={self.id!r}, chain={self.chain!r})"
        )


def _msgpack_default(obj: object) -> Any:
    """Coerce values msgpack can't pack on its own.

    Nu sentinels (EMPTY / INVALID) are first-class values: a Ref resolves to
    one when its address is absent or an operation didn't apply. The wire
    carries Nu values, so the display layer maps them to msgpack nil (which
    decodes to None / null on the browser) rather than crashing the
    connection.
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
        ref=d.get("ref") or (),
        payload=d.get("payload"),
        id=d.get("id"),
        chain=tuple((seg, typ, props or {}) for seg, typ, props in (d.get("chain") or ())),
    )
