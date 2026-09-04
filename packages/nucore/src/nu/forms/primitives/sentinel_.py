"""Sentinel interfaces - SentinelForm, EmptyForm, InvalidForm.

Wraps EMPTY and INVALID so they can appear as typed Form nodes in a Nu tree,
mainly so `is_empty()` / `is_invalid()` have something typed to call on.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from nu.lang import EMPTY, INVALID, Empty, Form, Invalid, Sentinel, TypedNu


__all__ = [
    "EmptyForm",
    "InvalidForm",
    "SentinelForm",
]


T = TypeVar("T", bound="Sentinel")


class SentinelForm(Form, TypedNu[T], Generic[T]):
    """Base for the sentinel interfaces, EmptyForm and InvalidForm."""


class EmptyForm(SentinelForm[Empty]):
    """Wraps EMPTY, the address-resolved-to-nothing sentinel.

    Example:
        >>> nu.run(nu.EmptyForm())[0]
        <EMPTY>
    """

    def __init__(self) -> None:
        """Build the node wrapping EMPTY. Takes no arguments."""
        super().__init__(EMPTY)


class InvalidForm(SentinelForm[Invalid]):
    """Wraps INVALID, the operation-not-applicable sentinel.

    Notes:
        - INVALID arises when an operation is applied to an EMPTY operand,
          and Query chains collapse to INVALID as soon as any operand is a
          sentinel. This Form does not produce that propagation itself, it
          just gives INVALID a typed node.

    Example:
        >>> nu.run(nu.InvalidForm())[0]
        <INVALID>
    """

    def __init__(self) -> None:
        """Build the node wrapping INVALID. Takes no arguments."""
        super().__init__(INVALID)
