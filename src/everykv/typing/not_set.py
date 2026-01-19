"""Used to indicate defaults arguments with "not set" semantics."""

from __future__ import annotations

from typing import TypeGuard


__all__ = [
    "NOT_SET",
    "NotSet",
    "is_notset",
]


class NotSet:
    """Sentinel for indicating a value argument is not provided."""

    def __repr__(self) -> str:
        """String representation for debugging."""
        return "<NotSet>"

    def __str__(self) -> str:
        """String representation for display."""
        return "NotSet"

    def __bool__(self) -> bool:
        """Boolean evaluation, always False."""
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NotSet)

    def __hash__(self) -> int:
        return hash("NotSet")


def is_notset(value: object) -> TypeGuard[NotSet]:
    """Check if value is NotSet sentinel."""
    return isinstance(value, NotSet)


NOT_SET = NotSet()
