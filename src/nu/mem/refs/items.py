"""mem leaves: one value at one key, read and written whole.

``ItemRef`` is the leaf itself (slot-level read, write and erase over one key
of a nested dict) and declares a slot once for every leaf. Each value leaf
mixes in the shape ref of its value (``shape.IntRef`` for an int), so the ref
is an operand of the value it names; the shape ref decides the surface, the
leaf decides where the value lives.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nu.domains import shape
from nu.domains.shape import MutableItemRef, Slot

from .base import RefBase


if TYPE_CHECKING:
    from nu.forms import None_
    from nu.lang import IntArg


__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ObjectRef",
    "StrRef",
]


class ItemRef(MutableItemRef, RefBase):
    """A single stored value in the dict substrate: read it, set it, erase it.

    The base every mem leaf builds on. It carries no value surface of its own;
    a leaf class mixes in the shape ref of the value it holds
    (``IntRef`` is this plus ``shape.IntRef``), and that one pairing is the
    whole of a leaf class.

    Args:
        address: this level's key, a literal or a Nu term yielding one.
    """

    @classmethod
    def slot(cls) -> Self:
        """Declare a slot holding this leaf."""
        return Slot(cls)  # type: ignore[return-value]


class ObjectRef(ItemRef, shape.ObjectRef):
    """A single stored value in the dict substrate, of no declared type.

    What a container descends to when its value is ``object``, undeclared, or
    a type with no mem leaf of its own. It carries the whole ``Object``
    surface, so the ref is still an operand: ``==`` builds an ``Eq``,
    attribute and subscript access descend into the value read, and a cast
    narrows it.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Yields:
        The stored value as it sits in the data dict.

    Example:
        >>> class Port(nu.Shape):
        ...     meta = nu.DictRef.slot(object)
        >>> ctx = nu.Context().bind(dict, {"meta": {"title": "hi"}}, Port)
        >>> nu.run(Port.meta["title"] == "hi", ctx)[0]
        True
    """


# =============================================================================
# TYPED REFS (with primitive Form interface)
# =============================================================================


class IntRef(ItemRef, shape.IntRef):
    """An int slot in the dict substrate, carrying the whole Int surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Every ``Int`` call is available on it, so the ref itself is an
          operand: ``User.age + 1`` builds arithmetic over the read.
        - The value is stored as a plain int, so the data dict stays
          JSON-shaped.

    Yields:
        The stored int.

    Example:
        >>> class User(nu.Shape):
        ...     age = nu.IntRef.slot()
        >>> ctx = nu.Context().bind(dict, {"age": 41}, User)
        >>> nu.run(User.age + 1, ctx)[0]
        42
    """

    def inc(self, step: IntArg = 1) -> None_:
        """Add ``step`` to the stored int and write the result back.

        Notes:
            - Read and write are two touches of the slot, not one atomic
              step; wrap it in a transaction when something else may write
              in between.
            - On an unwritten slot the read is NULL, so the addition
              raises TypeError. ``.init(0)`` the slot first.

        Example:
            >>> class User(nu.Shape):
            ...     age = nu.IntRef.slot()
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
            ...     age = nu.IntRef.slot()
            >>> data = {"age": 41}
            >>> ctx = nu.Context().bind(dict, data, User)
            >>> _ = nu.run(User.age.dec(2), ctx)
            >>> data
            {'age': 39}
        """
        return self.set(self - step)


class StrRef(ItemRef, shape.StrRef):
    """A str slot in the dict substrate, carrying the whole Str surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Every ``Str`` call is available on it, so ``User.name.upper()``
          reads the slot and builds the string op over it.

    Yields:
        The stored str.

    Example:
        >>> class User(nu.Shape):
        ...     name = nu.StrRef.slot()
        >>> ctx = nu.Context().bind(dict, {"name": "ada"}, User)
        >>> nu.run(User.name.upper(), ctx)[0]
        'ADA'
    """


class FloatRef(ItemRef, shape.FloatRef):
    """A float slot in the dict substrate, carrying the whole Float surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Nothing coerces on write: an int written here comes back an int.

    Yields:
        The stored float.

    Example:
        >>> class User(nu.Shape):
        ...     score = nu.FloatRef.slot()
        >>> ctx = nu.Context().bind(dict, {"score": 1.5}, User)
        >>> nu.run(User.score * 2, ctx)[0]
        3.0
    """


class BoolRef(ItemRef, shape.BoolRef):
    """A bool slot in the dict substrate, carrying the whole Bool surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - An unwritten slot reads NULL, which is not False; use
          ``.exists()`` when the difference matters.

    Yields:
        The stored bool.

    Example:
        >>> class User(nu.Shape):
        ...     active = nu.BoolRef.slot()
        >>> ctx = nu.Context().bind(dict, {"active": True}, User)
        >>> nu.run(User.active.not_(), ctx)[0]
        False
    """


class BytesRef(ItemRef, shape.BytesRef):
    """A bytes slot in the dict substrate, carrying the whole Bytes surface.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Stored as raw bytes, so a data dict holding one is no longer
          JSON-serialisable as it stands.

    Yields:
        The stored bytes.

    Example:
        >>> class Blob(nu.Shape):
        ...     body = nu.BytesRef.slot()
        >>> ctx = nu.Context().bind(dict, {"body": b"hi"}, Blob)
        >>> nu.run(Blob.body.decode(), ctx)[0]
        'hi'
    """
