"""MethodRef: leaf Ref naming a Method on a Service."""

from __future__ import annotations

from nu.lang import Ref


__all__ = ["MethodRef"]


class MethodRef(Ref):
    """A Ref addressing a Method on a Service. Leaf: address rides in _payload."""

    def __init__(
        self,
        *,
        name: str,
        owner_service: type | None = None,
        **payload: object,
    ) -> None:
        super().__init__()
        self._payload["name"] = name
        self._payload["owner_service"] = owner_service
        for k, v in payload.items():
            self._payload[k] = v
