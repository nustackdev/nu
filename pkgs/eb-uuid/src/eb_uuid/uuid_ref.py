"""UUID type for UUID values.

Pattern:
    UUIDType = TypeBase[UUID] + ComparableBase + UUID operations
    UUIDValue = ValueBase + UUIDType (computed results)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from everybase import Sentinel
from everybase.abc import (
    BytesValue,
    ComparableBase,
    IntValue,
    StrValue,
    TypeBase,
    ValueBase,
)


if TYPE_CHECKING:
    from everybase import Term

    from .args import UUIDArg


__all__ = [
    "UUIDType",
    "UUIDValue",
]


class UUIDType(
    ComparableBase["UUID | UUIDType"],
    TypeBase[UUID | Sentinel],
):
    """Abstract type for UUID operations.

    Supports UUID operations and comparison.
    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def uuid4(cls) -> UUIDValue:
        """Generate a random UUID (version 4)."""
        from everybase.abc import FuncCallOp

        return UUIDValue(FuncCallOp(uuid4))

    @classmethod
    def uuid1(
        cls,
        node: int | Term[int] | None = None,
        clock_seq: int | Term[int] | None = None,
    ) -> UUIDValue:
        """Generate a UUID from host ID and current time (version 1)."""
        from everybase.abc import FuncCallOp

        if node is not None and clock_seq is not None:
            return UUIDValue(FuncCallOp(uuid1, node, clock_seq))
        elif node is not None:
            return UUIDValue(FuncCallOp(uuid1, node))
        return UUIDValue(FuncCallOp(uuid1))

    @classmethod
    def uuid3(cls, namespace: UUIDArg, name: str | Term[str]) -> UUIDValue:
        """Generate a UUID based on MD5 hash of namespace and name (version 3)."""
        from everybase.abc import FuncCallOp

        if isinstance(namespace, UUID):
            namespace = UUIDValue(namespace)
        return UUIDValue(FuncCallOp(uuid3, namespace, name))

    @classmethod
    def uuid5(cls, namespace: UUIDArg, name: str | Term[str]) -> UUIDValue:
        """Generate a UUID based on SHA-1 hash of namespace and name (version 5)."""
        from everybase.abc import FuncCallOp

        if isinstance(namespace, UUID):
            namespace = UUIDValue(namespace)
        return UUIDValue(FuncCallOp(uuid5, namespace, name))

    @classmethod
    def from_str(cls, value: str | Term[str]) -> UUIDValue:
        """Create a UUIDValue from a string (hex with or without hyphens)."""
        from everybase.abc import FuncCallOp

        return UUIDValue(FuncCallOp(UUID, value))

    @classmethod
    def from_bytes(cls, b: bytes | Term[bytes]) -> UUIDValue:
        """Create a UUIDValue from 16 bytes."""
        from everybase.abc import FuncCallOp

        return UUIDValue(FuncCallOp(UUID, bytes=b))

    @classmethod
    def from_int(cls, value: int | Term[int]) -> UUIDValue:
        """Create a UUIDValue from a 128-bit integer."""
        from everybase.abc import FuncCallOp

        return UUIDValue(FuncCallOp(UUID, int=value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def version(self) -> IntValue:
        """Get the UUID version number (1, 3, 4, or 5)."""
        from everybase.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "version"))

    def variant(self) -> StrValue:
        """Get the UUID variant."""
        from everybase.abc import FuncCallOp

        return StrValue(FuncCallOp(getattr, self, "variant"))

    def time(self) -> IntValue:
        """Get the 60-bit timestamp (for UUID version 1)."""
        from everybase.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "time"))

    def clock_seq(self) -> IntValue:
        """Get the 14-bit clock sequence (for UUID version 1)."""
        from everybase.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "clock_seq"))

    def node(self) -> IntValue:
        """Get the 48-bit node (for UUID version 1)."""
        from everybase.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "node"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def hex(self) -> StrValue:
        """Get the UUID as a 32-character hexadecimal string."""
        from everybase.abc import FuncCallOp

        return StrValue(FuncCallOp(getattr, self, "hex"))

    def urn(self) -> StrValue:
        """Get the UUID as a URN (urn:uuid:...)."""
        from everybase.abc import FuncCallOp

        return StrValue(FuncCallOp(getattr, self, "urn"))

    def bytes(self) -> BytesValue:
        """Get the UUID as a 16-byte string."""
        from everybase.abc import FuncCallOp

        return BytesValue(FuncCallOp(getattr, self, "bytes"))

    def bytes_le(self) -> BytesValue:
        """Get the UUID as a 16-byte string in little-endian order."""
        from everybase.abc import FuncCallOp

        return BytesValue(FuncCallOp(getattr, self, "bytes_le"))

    def int_(self) -> IntValue:
        """Get the UUID as a 128-bit integer."""
        from everybase.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "int"))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class UUIDValue(ValueBase, UUIDType):
    """Computed UUID value (Python memory substrate)."""

    pass
