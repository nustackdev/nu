"""UUID ref base for UUID values.

UUIDRefBase = RefBase[UUID] + Comparable + UUID operations.
Stored as hex string for serialization.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING
from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from everybase.refs import RefBase
from everybase.traits import Comparable


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BytesRef, IntRef, StrRef

    from .args import UUIDArg
    from .py.refs import UUIDRef


__all__ = [
    "UUIDRefBase",
]


class UUIDRefBase(
    Comparable["UUID | UUIDRef"],
    RefBase[UUID],
    ABC,
):
    """Abstract base for UUID refs.

    Supports UUID operations and comparison. Stored as hex string format.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def uuid4(cls) -> UUIDRef:
        """Generate a random UUID (version 4)."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import UUIDRef

        return UUIDRef(FuncCallOp(uuid4))

    @classmethod
    def uuid1(
        cls,
        node: int | Term[int] | None = None,
        clock_seq: int | Term[int] | None = None,
    ) -> UUIDRef:
        """Generate a UUID from host ID and current time (version 1)."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import UUIDRef

        if node is not None and clock_seq is not None:
            return UUIDRef(FuncCallOp(uuid1, node, clock_seq))
        elif node is not None:
            return UUIDRef(FuncCallOp(uuid1, node))
        return UUIDRef(FuncCallOp(uuid1))

    @classmethod
    def uuid3(cls, namespace: UUIDArg, name: str | Term[str]) -> UUIDRef:
        """Generate a UUID based on MD5 hash of namespace and name (version 3)."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import UUIDRef

        if isinstance(namespace, UUID):
            namespace = UUIDRef(namespace)
        return UUIDRef(FuncCallOp(uuid3, namespace, name))

    @classmethod
    def uuid5(cls, namespace: UUIDArg, name: str | Term[str]) -> UUIDRef:
        """Generate a UUID based on SHA-1 hash of namespace and name (version 5)."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import UUIDRef

        if isinstance(namespace, UUID):
            namespace = UUIDRef(namespace)
        return UUIDRef(FuncCallOp(uuid5, namespace, name))

    @classmethod
    def from_str(cls, value: str | Term[str]) -> UUIDRef:
        """Create a UUIDRef from a string (hex with or without hyphens)."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import UUIDRef

        return UUIDRef(FuncCallOp(UUID, value))

    @classmethod
    def from_bytes(cls, b: bytes | Term[bytes]) -> UUIDRef:
        """Create a UUIDRef from 16 bytes."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import UUIDRef

        return UUIDRef(FuncCallOp(UUID, bytes=b))

    @classmethod
    def from_int(cls, value: int | Term[int]) -> UUIDRef:
        """Create a UUIDRef from a 128-bit integer."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import UUIDRef

        return UUIDRef(FuncCallOp(UUID, int=value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def version(self) -> IntRef:
        """Get the UUID version number (1, 3, 4, or 5)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "version"))

    def variant(self) -> StrRef:
        """Get the UUID variant."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import StrRef

        return StrRef(FuncCallOp(getattr, self, "variant"))

    def time(self) -> IntRef:
        """Get the 60-bit timestamp (for UUID version 1)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "time"))

    def clock_seq(self) -> IntRef:
        """Get the 14-bit clock sequence (for UUID version 1)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "clock_seq"))

    def node(self) -> IntRef:
        """Get the 48-bit node (for UUID version 1)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "node"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def hex(self) -> StrRef:
        """Get the UUID as a 32-character hexadecimal string."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import StrRef

        return StrRef(FuncCallOp(getattr, self, "hex"))

    def urn(self) -> StrRef:
        """Get the UUID as a URN (urn:uuid:...)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import StrRef

        return StrRef(FuncCallOp(getattr, self, "urn"))

    def bytes(self) -> BytesRef:
        """Get the UUID as a 16-byte string."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import BytesRef

        return BytesRef(FuncCallOp(getattr, self, "bytes"))

    def bytes_le(self) -> BytesRef:
        """Get the UUID as a 16-byte string in little-endian order."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import BytesRef

        return BytesRef(FuncCallOp(getattr, self, "bytes_le"))

    def int_(self) -> IntRef:
        """Get the UUID as a 128-bit integer."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "int"))
