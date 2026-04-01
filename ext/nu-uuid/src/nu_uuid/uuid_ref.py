"""UUID type for UUID values.

Pattern:
    UUIDType = Object[UUID] + ComparableBase + UUID operations
    UUIDValue = Interface + UUIDType (computed results)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from nu import Sentinel
from nu import (
    BytesI,
    ComparableBase,
    IntI,
    Object,
    StrI,
    Interface,
)


if TYPE_CHECKING:
    from nu import Nu

    from .args import UUIDArg


__all__ = [
    "UUIDType",
    "UUIDValue",
]


class UUIDType(
    ComparableBase["UUID | UUIDType"],
    Object[UUID | Sentinel],
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
        from nu import FuncCallOp

        return UUIDValue(FuncCallOp(uuid4))

    @classmethod
    def uuid1(
        cls,
        node: int | Nu[int] | None = None,
        clock_seq: int | Nu[int] | None = None,
    ) -> UUIDValue:
        """Generate a UUID from host ID and current time (version 1)."""
        from nu import FuncCallOp

        if node is not None and clock_seq is not None:
            return UUIDValue(FuncCallOp(uuid1, node, clock_seq))
        elif node is not None:
            return UUIDValue(FuncCallOp(uuid1, node))
        return UUIDValue(FuncCallOp(uuid1))

    @classmethod
    def uuid3(cls, namespace: UUIDArg, name: str | Nu[str]) -> UUIDValue:
        """Generate a UUID based on MD5 hash of namespace and name (version 3)."""
        from nu import FuncCallOp

        if isinstance(namespace, UUID):
            namespace = UUIDValue(namespace)
        return UUIDValue(FuncCallOp(uuid3, namespace, name))

    @classmethod
    def uuid5(cls, namespace: UUIDArg, name: str | Nu[str]) -> UUIDValue:
        """Generate a UUID based on SHA-1 hash of namespace and name (version 5)."""
        from nu import FuncCallOp

        if isinstance(namespace, UUID):
            namespace = UUIDValue(namespace)
        return UUIDValue(FuncCallOp(uuid5, namespace, name))

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> UUIDValue:
        """Create a UUIDValue from a string (hex with or without hyphens)."""
        from nu import FuncCallOp

        return UUIDValue(FuncCallOp(UUID, value))

    @classmethod
    def from_bytes(cls, b: bytes | Nu[bytes]) -> UUIDValue:
        """Create a UUIDValue from 16 bytes."""
        from nu import FuncCallOp

        return UUIDValue(FuncCallOp(UUID, bytes=b))

    @classmethod
    def from_int(cls, value: int | Nu[int]) -> UUIDValue:
        """Create a UUIDValue from a 128-bit integer."""
        from nu import FuncCallOp

        return UUIDValue(FuncCallOp(UUID, int=value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def version(self) -> IntI:
        """Get the UUID version number (1, 3, 4, or 5)."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "version"))

    def variant(self) -> StrI:
        """Get the UUID variant."""
        from nu import FuncCallOp

        return StrI(FuncCallOp(getattr, self, "variant"))

    def time(self) -> IntI:
        """Get the 60-bit timestamp (for UUID version 1)."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "time"))

    def clock_seq(self) -> IntI:
        """Get the 14-bit clock sequence (for UUID version 1)."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "clock_seq"))

    def node(self) -> IntI:
        """Get the 48-bit node (for UUID version 1)."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "node"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def hex(self) -> StrI:
        """Get the UUID as a 32-character hexadecimal string."""
        from nu import FuncCallOp

        return StrI(FuncCallOp(getattr, self, "hex"))

    def urn(self) -> StrI:
        """Get the UUID as a URN (urn:uuid:...)."""
        from nu import FuncCallOp

        return StrI(FuncCallOp(getattr, self, "urn"))

    def bytes(self) -> BytesI:
        """Get the UUID as a 16-byte string."""
        from nu import FuncCallOp

        return BytesI(FuncCallOp(getattr, self, "bytes"))

    def bytes_le(self) -> BytesI:
        """Get the UUID as a 16-byte string in little-endian order."""
        from nu import FuncCallOp

        return BytesI(FuncCallOp(getattr, self, "bytes_le"))

    def int_(self) -> IntI:
        """Get the UUID as a 128-bit integer."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "int"))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class UUIDValue(Interface, UUIDType):
    """Computed UUID value (Python memory substrate)."""

    pass
