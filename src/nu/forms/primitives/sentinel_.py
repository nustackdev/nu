"""Sentinel interfaces - SentinelForm, EmptyForm.

Wraps EMPTY so it can appear as a typed Form node in a Nu tree, mainly so
`is_empty()` has something typed to call on.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from nu.lang import EMPTY, Empty, Form, Sentinel, TypedNu


__all__ = [
    "EmptyForm",
    "SentinelForm",
]


T = TypeVar("T", bound="Sentinel")


class SentinelForm(Form, TypedNu[T], Generic[T]):
    """Base for the sentinel interfaces."""


class EmptyForm(SentinelForm[Empty]):
    """Wraps EMPTY, the no-value sentinel.

    Example:
        >>> nu.run(nu.EmptyForm())[0]
        <EMPTY>
    """

    def __init__(self) -> None:
        """Build the node wrapping EMPTY. Takes no arguments."""
        super().__init__(EMPTY)
