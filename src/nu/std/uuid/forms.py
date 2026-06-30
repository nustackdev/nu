"""UUID - the typed access surface for ``uuid.UUID``.

A ``UUID`` is a Nu term that carries a ``uuid.UUID``. Its operations split
the two ways the model intends:

- **accessors** (version, hex, bytes, ...) reuse the core ``GetAttrQuery`` atom -
  a UUID component is just an attribute read, and core already models that.
- **comparisons** reuse the core comparison atoms (``GtQuery`` ...).
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
    from nu.forms.primitives import BoolForm, BytesForm, IntForm, StrForm
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
    # COMPONENT ACCESSORS (reuse core GetAttrQuery)
    # =========================================================================

    def version(self) -> IntForm:
        """The version number (1, 3, 4, or 5)."""
        from nu import IntForm
        from nu.core import GetAttrQuery

        return IntForm(GetAttrQuery(self, "version"))

    def variant(self) -> StrForm:
        """The variant."""
        from nu import StrForm
        from nu.core import GetAttrQuery

        return StrForm(GetAttrQuery(self, "variant"))

    def time(self) -> IntForm:
        """The 60-bit timestamp (version 1)."""
        from nu import IntForm
        from nu.core import GetAttrQuery

        return IntForm(GetAttrQuery(self, "time"))

    def clock_seq(self) -> IntForm:
        """The 14-bit clock sequence (version 1)."""
        from nu import IntForm
        from nu.core import GetAttrQuery

        return IntForm(GetAttrQuery(self, "clock_seq"))

    def node(self) -> IntForm:
        """The 48-bit node (version 1)."""
        from nu import IntForm
        from nu.core import GetAttrQuery

        return IntForm(GetAttrQuery(self, "node"))

    # =========================================================================
    # CONVERSIONS (reuse core GetAttrQuery)
    # =========================================================================

    def hex(self) -> StrForm:
        """The UUID as a 32-character hex string."""
        from nu import StrForm
        from nu.core import GetAttrQuery

        return StrForm(GetAttrQuery(self, "hex"))

    def urn(self) -> StrForm:
        """The UUID as a URN (``urn:uuid:...``)."""
        from nu import StrForm
        from nu.core import GetAttrQuery

        return StrForm(GetAttrQuery(self, "urn"))

    def bytes(self) -> BytesForm:
        """The UUID as 16 bytes."""
        from nu import BytesForm
        from nu.core import GetAttrQuery

        return BytesForm(GetAttrQuery(self, "bytes"))

    def bytes_le(self) -> BytesForm:
        """The UUID as 16 bytes, little-endian."""
        from nu import BytesForm
        from nu.core import GetAttrQuery

        return BytesForm(GetAttrQuery(self, "bytes_le"))

    def int_(self) -> IntForm:
        """The UUID as a 128-bit integer."""
        from nu import IntForm
        from nu.core import GetAttrQuery

        return IntForm(GetAttrQuery(self, "int"))

    # =========================================================================
    # COMPARISON (reuse core comparison atoms)
    # =========================================================================

    def __gt__(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import GtQuery

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import LtQuery

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import GeQuery

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: UUIDArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import LeQuery

        return BoolForm(LeQuery(self, other))

    def eq(self, other: UUIDArg) -> BoolForm:
        """Whether two UUIDs are equal."""
        from nu import BoolForm
        from nu.core import EqQuery

        return BoolForm(EqQuery(self, other))

    def ne(self, other: UUIDArg) -> BoolForm:
        """Whether two UUIDs differ."""
        from nu import BoolForm
        from nu.core import NeQuery

        return BoolForm(NeQuery(self, other))
