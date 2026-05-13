"""Wire protocol between a nudle server and a nudle browser tab.

See projects/nu/stack/nudle/protocol.md in the Go space for the spec.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


__all__ = [
    "OP_ERROR",
    "OP_MOUNT",
    "OP_UNMOUNT",
    "Frame",
    "decode",
    "encode",
]


OP_MOUNT = "mount"
OP_UNMOUNT = "unmount"
OP_ERROR = "error"


@dataclass(frozen=True)
class Frame:
    """One wire envelope. Same shape both directions."""

    op: str
    ref: str = ""
    payload: Any = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"op": self.op, "ref": self.ref, "payload": self.payload}
        if self.id is not None:
            d["id"] = self.id
        return d


def encode(frame: Frame) -> str:
    return json.dumps(frame.to_dict())


def decode(raw: str) -> Frame:
    d = json.loads(raw)
    return Frame(
        op=d["op"],
        ref=d.get("ref", ""),
        payload=d.get("payload"),
        id=d.get("id"),
    )
