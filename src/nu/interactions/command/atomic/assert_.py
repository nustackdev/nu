"""Assert — Atomic Command that validates a condition during execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.terms import BinaryAtomic


if TYPE_CHECKING:
    from nu.terms import StrArg


__all__ = ["Assert"]


class Assert(BinaryAtomic):
    """Validate a condition during execution.

    Children: ``[condition, message]``

    Raises ``AssertionError`` when condition is falsy.
    """

    def __init__(self, condition: Any, message: StrArg = "Assertion failed") -> None:
        super().__init__(condition, message)

    def apply(self, condition: Any, message: Any) -> None:
        if not condition:
            raise AssertionError(message)
