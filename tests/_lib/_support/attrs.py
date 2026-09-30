"""Attrs helper: a Context whose names are already declared.

``attrs.set`` only reassigns a declared name. A test atom that writes attrs
imperatively from its own compile declares the names up front, the way a
binder would, and the names start out holding EMPTY.
"""

from __future__ import annotations

from nu.lang import EMPTY, Context


__all__ = ["declared"]


def declared(*names: str, **values: object) -> Context:
    """A Context with ``names`` bound to EMPTY and ``values`` bound as given."""
    return Context(attrs={**dict.fromkeys(names, EMPTY), **values})
