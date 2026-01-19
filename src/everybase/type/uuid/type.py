"""UUID Type."""

from __future__ import annotations

from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from everyterm.ops import FuncCallOp
from everyterm.term import BytesArg, IntArg, StrArg
from everyterm.types import BaseType, BytesType, ComparisonBase, IntType, StrType
from everyterm.typing import Sentinel

from .args import UUIDArg


__all__ = [
    "UUIDType",
]


class UUIDType(
    ComparisonBase["UUID | UUIDType"],
    BaseType[UUID | Sentinel],
):
    """Type representing a UUID.

    Supports UUID operations and comparison. Stored as string hex format.

    Example:
        >>> u = UUIDType.uuid4()
        >>> u.hex()      # StrType
        >>> u.version()  # IntType
        >>> u > other    # BoolType
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def uuid4(cls) -> UUIDType:
        """Generate a random UUID (version 4)."""
        return cls(FuncCallOp(uuid4))

    @classmethod
    def uuid1(cls, node: IntArg | None = None, clock_seq: IntArg | None = None) -> UUIDType:
        """Generate a UUID from host ID and current time (version 1)."""
        if node is not None and clock_seq is not None:
            return cls(FuncCallOp(uuid1, node, clock_seq))
        elif node is not None:
            return cls(FuncCallOp(uuid1, node))
        return cls(FuncCallOp(uuid1))

    @classmethod
    def uuid3(cls, namespace: UUIDArg, name: StrArg) -> UUIDType:
        """Generate a UUID based on MD5 hash of namespace and name (version 3)."""
        if isinstance(namespace, UUID):
            namespace = cls(namespace)
        return cls(FuncCallOp(uuid3, namespace, name))

    @classmethod
    def uuid5(cls, namespace: UUIDArg, name: StrArg) -> UUIDType:
        """Generate a UUID based on SHA-1 hash of namespace and name (version 5)."""
        if isinstance(namespace, UUID):
            namespace = cls(namespace)
        return cls(FuncCallOp(uuid5, namespace, name))

    @classmethod
    def from_str(cls, value: StrArg) -> UUIDType:
        """Create a UUIDType from a string (hex with or without hyphens)."""
        return cls(FuncCallOp(UUID, value))

    @classmethod
    def from_bytes(cls, b: BytesArg) -> UUIDType:
        """Create a UUIDType from 16 bytes."""
        return cls(FuncCallOp(UUID, bytes=b))

    @classmethod
    def from_int(cls, value: IntArg) -> UUIDType:
        """Create a UUIDType from a 128-bit integer."""
        return cls(FuncCallOp(UUID, int=value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def version(self) -> IntType:
        """Get the UUID version number (1, 3, 4, or 5)."""
        return IntType(FuncCallOp(getattr, self, "version"))

    def variant(self) -> StrType:
        """Get the UUID variant."""
        return StrType(FuncCallOp(getattr, self, "variant"))

    def time(self) -> IntType:
        """Get the 60-bit timestamp (for UUID version 1)."""
        return IntType(FuncCallOp(getattr, self, "time"))

    def clock_seq(self) -> IntType:
        """Get the 14-bit clock sequence (for UUID version 1)."""
        return IntType(FuncCallOp(getattr, self, "clock_seq"))

    def node(self) -> IntType:
        """Get the 48-bit node (for UUID version 1)."""
        return IntType(FuncCallOp(getattr, self, "node"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def hex(self) -> StrType:
        """Get the UUID as a 32-character hexadecimal string."""
        return StrType(FuncCallOp(getattr, self, "hex"))

    def urn(self) -> StrType:
        """Get the UUID as a URN (urn:uuid:...)."""
        return StrType(FuncCallOp(getattr, self, "urn"))

    def bytes(self) -> BytesType:
        """Get the UUID as a 16-byte string."""
        return BytesType(FuncCallOp(getattr, self, "bytes"))

    def bytes_le(self) -> BytesType:
        """Get the UUID as a 16-byte string in little-endian order."""
        return BytesType(FuncCallOp(getattr, self, "bytes_le"))

    def int_(self) -> IntType:
        """Get the UUID as a 128-bit integer."""
        return IntType(FuncCallOp(getattr, self, "int"))
