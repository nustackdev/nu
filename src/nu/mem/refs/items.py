"""Dict substrate item refs: typed value holders in nested dicts.

``ItemRef`` combines the shape ``MutableItemRef`` blueprint (slot-level CRUD)
with ``RefBase`` (dict navigation). Typed refs (``IntRef``, ``StrRef``, ...) add
the matching primitive Form so the value carries its full operator interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nu.domains.shape import MutableItemRef, Slot
from nu.forms import Bool, Bytes, Float, Int, None_, Str

from .base import RefBase


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, StrArg


__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "StrRef",
]


class ItemRef(MutableItemRef, RefBase):
    """A single stored value in the dict substrate, with no value interface.

    The untyped leaf: it reads, writes and erases one key, and carries the
    element type as metadata for whoever needs it, but exposes none of the
    operators a typed ref does. Reach for it when the held type is decided by
    a container above (``ListRef[i]`` and ``DictRef[k]`` both descend into
    one) rather than declared on a Shape.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The type carried is metadata only: nothing coerces or rejects a
          value on write, and nothing checks what comes back on read.

    Example:
        >>> class Port(nu.Shape):
        ...     tags = nu.mem.ListRef.slot(str)
        >>> ctx = nu.Context().bind(dict, {"tags": ["a", "b"]}, Port)
        >>> nu.run(Port.tags[1], ctx)[0]
        'b'
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        value_type: type,
        value_value_type: type,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["value_type"] = value_type
        self._payload["value_value_type"] = value_value_type

    @classmethod
    def slot(cls, value_type: type, value_value_type: type) -> Self:
        """Declare an untyped item slot holding ``value_type`` values.

        Args:
            value_type: the Python type the slot holds.
            value_value_type: the Nu Form matching ``value_type``.

        Notes:
            - Written in a Shape class body; the metaclass turns it into a
              bound ``ItemRef`` addressed by the attribute name.

        Example:
            class Row(Shape):
                cell = ItemRef.slot(int, Int)
        """
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore[return-value]


# =============================================================================
# TYPED REFS (with primitive Form interface)
# =============================================================================


class IntRef(ItemRef, Int):
    """An int slot in the dict substrate, carrying the whole Int surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Every ``Int`` call is available on it, so the ref itself is an
          operand: ``User.age + 1`` builds arithmetic over the read.
        - The value is stored as a plain int, so the data dict stays
          JSON-shaped.

    Yields:
        The stored int. EMPTY when the slot was never written or its path is
        broken.

    Example:
        >>> class User(nu.Shape):
        ...     age = nu.mem.IntRef.slot()
        >>> ctx = nu.Context().bind(dict, {"age": 41}, User)
        >>> nu.run(User.age + 1, ctx)[0]
        42
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=int,
            value_value_type=Int,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    def inc(self, step: IntArg = 1) -> None_:
        """Add ``step`` to the stored int and write the result back.

        Notes:
            - Read and write are two touches of the slot, not one atomic
              step; wrap it in a transaction when something else may write
              in between.
            - On an unwritten slot the read is EMPTY, so the addition is
              INVALID and that is what gets stored.

        Example:
            >>> class User(nu.Shape):
            ...     age = nu.mem.IntRef.slot()
            >>> data = {"age": 41}
            >>> ctx = nu.Context().bind(dict, data, User)
            >>> _ = nu.run(User.age.inc(), ctx)
            >>> data
            {'age': 42}
        """
        return self.set(self + step)

    def dec(self, step: IntArg = 1) -> None_:
        """Subtract ``step`` from the stored int and write the result back.

        Notes:
            - Same two-touch read-then-write as :meth:`inc`.

        Example:
            >>> class User(nu.Shape):
            ...     age = nu.mem.IntRef.slot()
            >>> data = {"age": 41}
            >>> ctx = nu.Context().bind(dict, data, User)
            >>> _ = nu.run(User.age.dec(2), ctx)
            >>> data
            {'age': 39}
        """
        return self.set(self - step)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare an int slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef, Str):
    """A str slot in the dict substrate, carrying the whole Str surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Every ``Str`` call is available on it, so ``User.name.upper()``
          reads the slot and builds the string op over it.

    Yields:
        The stored str. EMPTY when the slot was never written or its path is
        broken.

    Example:
        >>> class User(nu.Shape):
        ...     name = nu.mem.StrRef.slot()
        >>> ctx = nu.Context().bind(dict, {"name": "ada"}, User)
        >>> nu.run(User.name.upper(), ctx)[0]
        'ADA'
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a str slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef, Float):
    """A float slot in the dict substrate, carrying the whole Float surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Nothing coerces on write: an int written here comes back an int.

    Yields:
        The stored float. EMPTY when the slot was never written or its path
        is broken.

    Example:
        >>> class User(nu.Shape):
        ...     score = nu.mem.FloatRef.slot()
        >>> ctx = nu.Context().bind(dict, {"score": 1.5}, User)
        >>> nu.run(User.score * 2, ctx)[0]
        3.0
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=float,
            value_value_type=Float,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a float slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef, Bool):
    """A bool slot in the dict substrate, carrying the whole Bool surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - An unwritten slot reads EMPTY, which is not False; use
          ``.exists()`` when the difference matters.

    Yields:
        The stored bool. EMPTY when the slot was never written or its path is
        broken.

    Example:
        >>> class User(nu.Shape):
        ...     active = nu.mem.BoolRef.slot()
        >>> ctx = nu.Context().bind(dict, {"active": True}, User)
        >>> nu.run(User.active.not_(), ctx)[0]
        False
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=bool,
            value_value_type=Bool,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a bool slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef, Bytes):
    """A bytes slot in the dict substrate, carrying the whole Bytes surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Stored as raw bytes, so a data dict holding one is no longer
          JSON-serialisable as it stands.

    Yields:
        The stored bytes. EMPTY when the slot was never written or its path
        is broken.

    Example:
        >>> class Blob(nu.Shape):
        ...     body = nu.mem.BytesRef.slot()
        >>> ctx = nu.Context().bind(dict, {"body": b"hi"}, Blob)
        >>> nu.run(Blob.body.decode(), ctx)[0]
        'hi'
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=bytes,
            value_value_type=Bytes,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a bytes slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]
