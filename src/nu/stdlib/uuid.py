"""UUID interface - typed wrapper for uuid.UUID.

_UUIDI provides UUID operations (constructors, accessors, conversions, comparison).
UUIDI is the leaf: _UUIDI + TypedNu[UUID].
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from nu import Arg, Nu
    from nu.primitives import BoolI, BytesI, IntI, StrI


__all__ = ["UUIDI", "UUIDArg"]


type UUIDArg = Arg[UUID]


class _UUIDI(Interface):
    """UUID operations mixin - constructors, accessors, conversions, comparison."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def uuid4(cls) -> UUIDI:
        """Generate a random UUID (version 4)."""
        from nu import FuncCall

        return UUIDI(FuncCall(uuid4))

    @classmethod
    def uuid1(
        cls,
        node: int | Nu[int] | None = None,
        clock_seq: int | Nu[int] | None = None,
    ) -> UUIDI:
        """Generate a UUID from host ID and current time (version 1)."""
        from nu import FuncCall

        if node is not None and clock_seq is not None:
            return UUIDI(FuncCall(uuid1, node, clock_seq))
        elif node is not None:
            return UUIDI(FuncCall(uuid1, node))
        return UUIDI(FuncCall(uuid1))

    @classmethod
    def uuid3(cls, namespace: UUIDArg, name: str | Nu[str]) -> UUIDI:
        """Generate a UUID based on MD5 hash of namespace and name (version 3)."""
        from nu import FuncCall

        if isinstance(namespace, UUID):
            namespace = UUIDI(namespace)
        return UUIDI(FuncCall(uuid3, namespace, name))

    @classmethod
    def uuid5(cls, namespace: UUIDArg, name: str | Nu[str]) -> UUIDI:
        """Generate a UUID based on SHA-1 hash of namespace and name (version 5)."""
        from nu import FuncCall

        if isinstance(namespace, UUID):
            namespace = UUIDI(namespace)
        return UUIDI(FuncCall(uuid5, namespace, name))

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> UUIDI:
        """Create a UUIDI from a string (hex with or without hyphens)."""
        from nu import FuncCall

        return UUIDI(FuncCall(UUID, value))

    @classmethod
    def from_bytes(cls, b: bytes | Nu[bytes]) -> UUIDI:
        """Create a UUIDI from 16 bytes."""
        from nu import FuncCall

        return UUIDI(FuncCall(UUID, bytes=b))

    @classmethod
    def from_int(cls, value: int | Nu[int]) -> UUIDI:
        """Create a UUIDI from a 128-bit integer."""
        from nu import FuncCall

        return UUIDI(FuncCall(UUID, int=value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def version(self) -> IntI:
        """Get the UUID version number (1, 3, 4, or 5)."""
        from nu import FuncCall, IntI

        return IntI(FuncCall(getattr, self, "version"))

    def variant(self) -> StrI:
        """Get the UUID variant."""
        from nu import FuncCall, StrI

        return StrI(FuncCall(getattr, self, "variant"))

    def time(self) -> IntI:
        """Get the 60-bit timestamp (for UUID version 1)."""
        from nu import FuncCall, IntI

        return IntI(FuncCall(getattr, self, "time"))

    def clock_seq(self) -> IntI:
        """Get the 14-bit clock sequence (for UUID version 1)."""
        from nu import FuncCall, IntI

        return IntI(FuncCall(getattr, self, "clock_seq"))

    def node(self) -> IntI:
        """Get the 48-bit node (for UUID version 1)."""
        from nu import FuncCall, IntI

        return IntI(FuncCall(getattr, self, "node"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def hex(self) -> StrI:
        """Get the UUID as a 32-character hexadecimal string."""
        from nu import FuncCall, StrI

        return StrI(FuncCall(getattr, self, "hex"))

    def urn(self) -> StrI:
        """Get the UUID as a URN (urn:uuid:...)."""
        from nu import FuncCall, StrI

        return StrI(FuncCall(getattr, self, "urn"))

    def bytes(self) -> BytesI:
        """Get the UUID as a 16-byte string."""
        from nu import BytesI, FuncCall

        return BytesI(FuncCall(getattr, self, "bytes"))

    def bytes_le(self) -> BytesI:
        """Get the UUID as a 16-byte string in little-endian order."""
        from nu import BytesI, FuncCall

        return BytesI(FuncCall(getattr, self, "bytes_le"))

    def int_(self) -> IntI:
        """Get the UUID as a 128-bit integer."""
        from nu import FuncCall, IntI

        return IntI(FuncCall(getattr, self, "int"))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: UUIDArg) -> BoolI:
        from nu import BoolI, Gt

        return BoolI(Gt(self, other))

    def __lt__(self, other: UUIDArg) -> BoolI:
        from nu import BoolI, Lt

        return BoolI(Lt(self, other))

    def __ge__(self, other: UUIDArg) -> BoolI:
        from nu import BoolI, Ge

        return BoolI(Ge(self, other))

    def __le__(self, other: UUIDArg) -> BoolI:
        from nu import BoolI, Le

        return BoolI(Le(self, other))

    def eq(self, other: UUIDArg) -> BoolI:
        from nu import BoolI, Eq

        return BoolI(Eq(self, other))

    def ne(self, other: UUIDArg) -> BoolI:
        from nu import BoolI, Ne

        return BoolI(Ne(self, other))


# =============================================================================
# LEAF
# =============================================================================


class UUIDI(_UUIDI, TypedNu[UUID]):
    """UUID leaf - _UUIDI + TypedNu[UUID]."""

    pass
