"""Attrs helper: a Context whose names are already declared.

``.set()`` only reassigns a declared name. A test that reads its writes back off
the Context a run returns declares them up front, the way an enclosing ``Let``
would, and the names start out holding EMPTY.
"""

from __future__ import annotations

from nu.lang import EMPTY, Context


__all__ = ["declared"]


def declared(*names: str, **values: object) -> Context:
    """A Context with ``names`` bound to EMPTY and ``values`` bound as given."""
    ctx = Context()
    for name in names:
        ctx.attrs[name] = EMPTY
    for name, value in values.items():
        ctx.attrs[name] = value
    return ctx
