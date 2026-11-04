"""NullForm: NULL as a typed Form node in a Nu tree."""

from __future__ import annotations

from nu.lang import NULL, Form, Null, TypedNu


__all__ = [
    "NullForm",
]


class NullForm(Form, TypedNu[Null]):
    """Wraps NULL, the value an absent read gives.

    Example:
        >>> nu.run(nu.NullForm())[0]
        <NULL>
    """

    def __init__(self) -> None:
        """Build the node wrapping NULL. Takes no arguments."""
        super().__init__(NULL)
