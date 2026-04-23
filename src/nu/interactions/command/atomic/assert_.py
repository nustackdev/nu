"""Assert — Atomic Command that validates a condition during execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms import BinaryCommand, Mode


if TYPE_CHECKING:
    from nu.terms import StrArg


__all__ = ["Assert"]


class Assert(BinaryCommand):
    """Validate a condition during execution.

    Children: ``[condition, message]``

    Raises ``AssertionError`` when condition is falsy.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(self, condition: Any, message: StrArg = "Assertion failed") -> None:
        super().__init__(condition, message)

    def apply(self, condition: Any, message: Any) -> None:
        if not condition:
            raise AssertionError(message)
