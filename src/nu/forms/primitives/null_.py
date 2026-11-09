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

    @classmethod
    def create(cls) -> NullForm:
        """A NULL term, so a branch can yield NULL like any other value.

        Yields:
            NULL. Writes refuse it, reads downstream see an absent value.

        Example:
            >>> nu.run(nu.If(False, nu.Int(1), nu.NullForm.create()))[0]
            <NULL>
        """
        return cls()
