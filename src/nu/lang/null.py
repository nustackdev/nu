"""NULL: the value a context read gives when nothing is there.

nu is persistent and shared across processes, so an absent slot is a normal
state. The rules:

- Born only at a context read (a Ref, a context lookup) that finds nothing.
  Pure ops never make NULL; they act like Python (raise, or take a default).
- Ops have no NULL handling. They run the plain Python op and NULL's own
  interface decides: ``==``, ``!=``, ``hash``, ``repr`` and ``bool`` (False)
  work, anything else (``len``, ``iter``, ``in``, arithmetic, indexing)
  raises TypeError, and ``str()`` raises TypeError on purpose. ``len``,
  ``iter`` and ``in`` name the path in their message.
- All NULLs are equal, whatever their hint. ``NULL == None`` is False: a
  stored None and an absent slot never compare equal.
- The hint is the dotted path the read came from, for errors and repr only.
  Test with ``is_null()``, never with ``is NULL``.
- Writes refuse NULL. Absence is made by erasing, not by writing NULL.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeGuard


if TYPE_CHECKING:
    from collections.abc import Iterator


__all__ = [
    "NULL",
    "Null",
    "is_null",
]


class Null:
    """No value at this address. Falsy, equal to every other Null, never to None."""

    __slots__ = ("hint",)

    def __init__(self, hint: str = "") -> None:
        self.hint = hint

    def __repr__(self) -> str:
        return f"<NULL {self.hint}>" if self.hint else "<NULL>"

    def __str__(self) -> str:
        where = f" at {self.hint}" if self.hint else ""
        raise TypeError(f"NULL has no string form (nothing is stored{where})")

    def __bool__(self) -> bool:
        return False

    def __len__(self) -> int:
        raise TypeError(f"len() of {self!r}: nothing is stored here")

    def __iter__(self) -> Iterator[object]:
        raise TypeError(f"iteration over {self!r}: nothing is stored here")

    def __contains__(self, item: object) -> bool:
        raise TypeError(f"'in' on {self!r}: nothing is stored here")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Null)

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Null)

    def __hash__(self) -> int:
        return hash(Null)

    def __reduce__(self) -> tuple[type[Null], tuple[str]]:
        return (Null, (self.hint,))


NULL: Null = Null()


def is_null(value: object) -> TypeGuard[Null]:
    """True if ``value`` is a NULL, whatever its hint."""
    return isinstance(value, Null)
