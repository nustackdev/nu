"""UUID interface - typed wrapper for uuid.UUID.

_UUIDI provides UUID operations (constructors, accessors, conversions, comparison).
UUIDI is the leaf: _UUIDI + TypedNu[UUID].
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from nu.terms import Form, Mode, TypedNu


if TYPE_CHECKING:
    from nu import Arg, Nu
    from nu.forms.primitives import BoolForm, BytesForm, IntForm, StrForm


__all__ = ["UUIDI", "UUIDArg"]


type UUIDArg = Arg[UUID]


class _UUIDI(Form):
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

    def version(self) -> IntForm:
        """Get the UUID version number (1, 3, 4, or 5)."""
        from nu import FuncCall, IntForm

        return IntForm(FuncCall(getattr, self, "version"))

    def variant(self) -> StrForm:
        """Get the UUID variant."""
        from nu import FuncCall, StrForm

        return StrForm(FuncCall(getattr, self, "variant"))

    def time(self) -> IntForm:
        """Get the 60-bit timestamp (for UUID version 1)."""
        from nu import FuncCall, IntForm

        return IntForm(FuncCall(getattr, self, "time"))

    def clock_seq(self) -> IntForm:
        """Get the 14-bit clock sequence (for UUID version 1)."""
        from nu import FuncCall, IntForm

        return IntForm(FuncCall(getattr, self, "clock_seq"))

    def node(self) -> IntForm:
        """Get the 48-bit node (for UUID version 1)."""
        from nu import FuncCall, IntForm

        return IntForm(FuncCall(getattr, self, "node"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def hex(self) -> StrForm:
        """Get the UUID as a 32-character hexadecimal string."""
        from nu import FuncCall, StrForm

        return StrForm(FuncCall(getattr, self, "hex"))

    def urn(self) -> StrForm:
        """Get the UUID as a URN (urn:uuid:...)."""
        from nu import FuncCall, StrForm

        return StrForm(FuncCall(getattr, self, "urn"))

    def bytes(self) -> BytesForm:
        """Get the UUID as a 16-byte string."""
        from nu import BytesForm, FuncCall

        return BytesForm(FuncCall(getattr, self, "bytes"))

    def bytes_le(self) -> BytesForm:
        """Get the UUID as a 16-byte string in little-endian order."""
        from nu import BytesForm, FuncCall

        return BytesForm(FuncCall(getattr, self, "bytes_le"))

    def int_(self) -> IntForm:
        """Get the UUID as a 128-bit integer."""
        from nu import FuncCall, IntForm

        return IntForm(FuncCall(getattr, self, "int"))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm, Gt

        return BoolForm(Gt(self, other))

    def __lt__(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm, Lt

        return BoolForm(Lt(self, other))

    def __ge__(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm, Ge

        return BoolForm(Ge(self, other))

    def __le__(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm, Le

        return BoolForm(Le(self, other))

    def eq(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm, Eq

        return BoolForm(Eq(self, other))

    def ne(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm, Ne

        return BoolForm(Ne(self, other))


# =============================================================================
# LEAF
# =============================================================================


class UUIDI(_UUIDI, TypedNu[UUID]):
    """UUID leaf - _UUIDI + TypedNu[UUID]."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
