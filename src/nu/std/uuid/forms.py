"""UUID - the typed access surface for ``uuid.UUID``.

A ``UUID`` is a Nu term that carries a ``uuid.UUID``. Its operations split
the two ways the model intends:

- **accessors** (version, hex, bytes, ...) reuse the core ``GetAttr`` atom -
  a UUID component is just an attribute read, and core already models that.
- **comparisons** reuse the core comparison atoms (``Gt`` ...).
- **constructors** are the one thing core can't do, so they wrap the new atoms
  from ``interactions``.

That's the whole pattern: Form for access, interactions for the calls, reusing
core wherever it already expresses the op.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID as _UUID

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.primitives import Bool, Bytes, Int, Str
    from nu.lang import Arg, BytesArg, IntArg, StrArg

    type UUIDArg = Arg[_UUID]


__all__ = ["UUID"]


class UUID(Form, TypedNu[_UUID]):
    """UUID interface - the ``uuid.UUID`` class as a Form.

    Mirrors the class surface only: the ``UUID(...)`` constructor (the
    ``from_*`` alternate constructors below) plus instance ops (accessors,
    conversions, comparison). The module-level generators ``uuid1`` / ``uuid3``
    / ``uuid4`` / ``uuid5`` are NOT methods here - they live in ``functions`` as
    free functions, matching the stdlib layout.
    """

    # =========================================================================
    # ALTERNATE CONSTRUCTORS (the ``UUID(...)`` class constructor; new atoms)
    # =========================================================================

    @classmethod
    def from_str(cls, value: StrArg) -> UUID:
        """Parse a hex string (with or without hyphens) into a UUID."""
        from .interactions import UuidFromStrQuery

        return UUID(UuidFromStrQuery(value))

    @classmethod
    def from_bytes(cls, value: BytesArg) -> UUID:
        """Build a UUID from 16 bytes."""
        from .interactions import UuidFromBytesQuery

        return UUID(UuidFromBytesQuery(value))

    @classmethod
    def from_int(cls, value: IntArg) -> UUID:
        """Build a UUID from a 128-bit integer."""
        from .interactions import UuidFromIntQuery

        return UUID(UuidFromIntQuery(value))

    # =========================================================================
    # COMPONENT ACCESSORS (reuse core GetAttr)
    # =========================================================================

    def version(self) -> Int:
        """The version number (1, 3, 4, or 5)."""
        from nu import Int
        from nu.core import GetAttr

        return Int(GetAttr(self, "version"))

    def variant(self) -> Str:
        """The variant."""
        from nu import Str
        from nu.core import GetAttr

        return Str(GetAttr(self, "variant"))

    def time(self) -> Int:
        """The 60-bit timestamp (version 1)."""
        from nu import Int
        from nu.core import GetAttr

        return Int(GetAttr(self, "time"))

    def clock_seq(self) -> Int:
        """The 14-bit clock sequence (version 1)."""
        from nu import Int
        from nu.core import GetAttr

        return Int(GetAttr(self, "clock_seq"))

    def node(self) -> Int:
        """The 48-bit node (version 1)."""
        from nu import Int
        from nu.core import GetAttr

        return Int(GetAttr(self, "node"))

    # =========================================================================
    # CONVERSIONS (reuse core GetAttr)
    # =========================================================================

    def hex(self) -> Str:
        """The UUID as a 32-character hex string."""
        from nu import Str
        from nu.core import GetAttr

        return Str(GetAttr(self, "hex"))

    def urn(self) -> Str:
        """The UUID as a URN (``urn:uuid:...``)."""
        from nu import Str
        from nu.core import GetAttr

        return Str(GetAttr(self, "urn"))

    def bytes(self) -> Bytes:
        """The UUID as 16 bytes."""
        from nu import Bytes
        from nu.core import GetAttr

        return Bytes(GetAttr(self, "bytes"))

    def bytes_le(self) -> Bytes:
        """The UUID as 16 bytes, little-endian."""
        from nu import Bytes
        from nu.core import GetAttr

        return Bytes(GetAttr(self, "bytes_le"))

    def int_(self) -> Int:
        """The UUID as a 128-bit integer."""
        from nu import Int
        from nu.core import GetAttr

        return Int(GetAttr(self, "int"))

    # =========================================================================
    # COMPARISON (reuse core comparison atoms)
    # =========================================================================

    def __gt__(self, other: UUIDArg) -> Bool:
        from nu import Bool
        from nu.core import Gt

        return Bool(Gt(self, other))

    def __lt__(self, other: UUIDArg) -> Bool:
        from nu import Bool
        from nu.core import Lt

        return Bool(Lt(self, other))

    def __ge__(self, other: UUIDArg) -> Bool:
        from nu import Bool
        from nu.core import Ge

        return Bool(Ge(self, other))

    def __le__(self, other: UUIDArg) -> Bool:
        from nu import Bool
        from nu.core import Le

        return Bool(Le(self, other))

    def eq(self, other: UUIDArg) -> Bool:
        """Whether two UUIDs are equal."""
        from nu import Bool
        from nu.core import Eq

        return Bool(Eq(self, other))

    def ne(self, other: UUIDArg) -> Bool:
        """Whether two UUIDs differ."""
        from nu import Bool
        from nu.core import Ne

        return Bool(Ne(self, other))
