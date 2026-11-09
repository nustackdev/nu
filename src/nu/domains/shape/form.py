"""What every shape form shares: a slot-level surface laid over a value form.

A shape form is one cell of the shape grid: a value form from ``nu.forms``
(the Python type) under a capability base (read, mutable, reactive). The
capability belongs to the slot, never to the value it holds, so a value read
off a shape form drops back to the plain value form.
"""

from __future__ import annotations

from nu.lang import Form, Ref, TypedNu


__all__ = ["SlotForm"]


class SlotForm(Form):
    """Base of every shape capability form (``ItemForm``, ``CollectionForm`` and their tiers)."""

    def _value_form(self) -> type[Form]:
        """The value form under this cell, past the shape tiers and any Ref.

        ``fallback`` wraps its result in this form, and a fallback value is a
        value: it has no slot to set, erase or watch.
        """
        from nu.forms import Object

        for cls in type(self).__mro__:
            if (
                issubclass(cls, TypedNu)
                and issubclass(cls, Form)
                and not issubclass(cls, (Ref, SlotForm))
            ):
                return cls
        return Object
