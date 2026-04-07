"""UUID interface - typed wrapper for uuid.UUID.

_UUIDI provides UUID operations (constructors, accessors, conversions, comparison).
UUIDI is the leaf: _UUIDI + TypedNu[UUID].
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from nu.interface import Interface, TypedNu


if TYPE_CHECKING:
    from nu import Arg, Nu

    from nu.primitives import BoolI, BytesI, IntI, StrI


__all__ = ["UUIDArg", "UUIDI"]


type UUIDArg = Arg[UUID]


class _UUIDI(Interface):
    """UUID operations mixin - constructors, accessors, conversions, comparison."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def uuid4(cls) -> UUIDI:
        """Generate a random UUID (version 4)."""
        from nu import FuncCallOp

        return UUIDI(FuncCallOp(uuid4))

    @classmethod
    def uuid1(
        cls,
        node: int | Nu[int] | None = None,
        clock_seq: int | Nu[int] | None = None,
    ) -> UUIDI:
        """Generate a UUID from host ID and current time (version 1)."""
        from nu import FuncCallOp

        if node is not None and clock_seq is not None:
            return UUIDI(FuncCallOp(uuid1, node, clock_seq))
        elif node is not None:
            return UUIDI(FuncCallOp(uuid1, node))
        return UUIDI(FuncCallOp(uuid1))

    @classmethod
    def uuid3(cls, namespace: UUIDArg, name: str | Nu[str]) -> UUIDI:
        """Generate a UUID based on MD5 hash of namespace and name (version 3)."""
        from nu import FuncCallOp

        if isinstance(namespace, UUID):
            namespace = UUIDI(namespace)
        return UUIDI(FuncCallOp(uuid3, namespace, name))

    @classmethod
    def uuid5(cls, namespace: UUIDArg, name: str | Nu[str]) -> UUIDI:
        """Generate a UUID based on SHA-1 hash of namespace and name (version 5)."""
        from nu import FuncCallOp

        if isinstance(namespace, UUID):
            namespace = UUIDI(namespace)
        return UUIDI(FuncCallOp(uuid5, namespace, name))

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> UUIDI:
        """Create a UUIDI from a string (hex with or without hyphens)."""
        from nu import FuncCallOp

        return UUIDI(FuncCallOp(UUID, value))

    @classmethod
    def from_bytes(cls, b: bytes | Nu[bytes]) -> UUIDI:
        """Create a UUIDI from 16 bytes."""
        from nu import FuncCallOp

        return UUIDI(FuncCallOp(UUID, bytes=b))

    @classmethod
    def from_int(cls, value: int | Nu[int]) -> UUIDI:
        """Create a UUIDI from a 128-bit integer."""
        from nu import FuncCallOp

        return UUIDI(FuncCallOp(UUID, int=value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def version(self) -> IntI:
        """Get the UUID version number (1, 3, 4, or 5)."""
        from nu import FuncCallOp
        from nu import IntI

        return IntI(FuncCallOp(getattr, self, "version"))

    def variant(self) -> StrI:
        """Get the UUID variant."""
        from nu import FuncCallOp
        from nu import StrI

        return StrI(FuncCallOp(getattr, self, "variant"))

    def time(self) -> IntI:
        """Get the 60-bit timestamp (for UUID version 1)."""
        from nu import FuncCallOp
        from nu import IntI

        return IntI(FuncCallOp(getattr, self, "time"))

    def clock_seq(self) -> IntI:
        """Get the 14-bit clock sequence (for UUID version 1)."""
        from nu import FuncCallOp
        from nu import IntI

        return IntI(FuncCallOp(getattr, self, "clock_seq"))

    def node(self) -> IntI:
        """Get the 48-bit node (for UUID version 1)."""
        from nu import FuncCallOp
        from nu import IntI

        return IntI(FuncCallOp(getattr, self, "node"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def hex(self) -> StrI:
        """Get the UUID as a 32-character hexadecimal string."""
        from nu import FuncCallOp
        from nu import StrI

        return StrI(FuncCallOp(getattr, self, "hex"))

    def urn(self) -> StrI:
        """Get the UUID as a URN (urn:uuid:...)."""
        from nu import FuncCallOp
        from nu import StrI

        return StrI(FuncCallOp(getattr, self, "urn"))

    def bytes(self) -> BytesI:
        """Get the UUID as a 16-byte string."""
        from nu import FuncCallOp
        from nu import BytesI

        return BytesI(FuncCallOp(getattr, self, "bytes"))

    def bytes_le(self) -> BytesI:
        """Get the UUID as a 16-byte string in little-endian order."""
        from nu import FuncCallOp
        from nu import BytesI

        return BytesI(FuncCallOp(getattr, self, "bytes_le"))

    def int_(self) -> IntI:
        """Get the UUID as a 128-bit integer."""
        from nu import FuncCallOp
        from nu import IntI

        return IntI(FuncCallOp(getattr, self, "int"))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: UUIDArg) -> BoolI:
        from nu import GtOp
        from nu import BoolI

        return BoolI(GtOp(self, other))

    def __lt__(self, other: UUIDArg) -> BoolI:
        from nu import LtOp
        from nu import BoolI

        return BoolI(LtOp(self, other))

    def __ge__(self, other: UUIDArg) -> BoolI:
        from nu import GeOp
        from nu import BoolI

        return BoolI(GeOp(self, other))

    def __le__(self, other: UUIDArg) -> BoolI:
        from nu import LeOp
        from nu import BoolI

        return BoolI(LeOp(self, other))

    def eq(self, other: UUIDArg) -> BoolI:
        from nu import EqOp
        from nu import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: UUIDArg) -> BoolI:
        from nu import NeOp
        from nu import BoolI

        return BoolI(NeOp(self, other))


# =============================================================================
# LEAF
# =============================================================================


class UUIDI(_UUIDI, TypedNu[UUID]):
    """UUID leaf - _UUIDI + TypedNu[UUID]."""

    pass
