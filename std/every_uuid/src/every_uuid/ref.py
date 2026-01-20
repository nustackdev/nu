"""UUID Ref."""

from __future__ import annotations

from uuid import UUID

from term.ops import MethodCallOp
from term.types import BytesType, IntType, StrType

from every._abc import StrArg
from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef

from .args import UUIDArg
from .type import UUIDType


__all__ = [
    "UUIDRef",
]


class UUIDRef(CollectionItemRefBase[UUID, UUIDType], PrimitiveRef):
    """Reference to a UUID value in storage."""

    def set(self, value: UUIDArg | StrArg) -> UUIDType:
        """Set the UUID value."""
        if isinstance(value, UUID):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")

        return UUIDType(TypedSetCmd(self, val))

    def get(self) -> UUIDType:
        """Get the UUID value."""
        return UUIDType.from_str(GetOp(self))

    # =========================================================================
    # CONVENIENCE METHODS (delegate to get())
    # =========================================================================

    def hex(self) -> StrType:
        return self.get().hex()

    def urn(self) -> StrType:
        return self.get().urn()

    def bytes(self) -> BytesType:
        return self.get().bytes()

    def version(self) -> IntType:
        return self.get().version()

    def int_(self) -> IntType:
        return self.get().int_()
