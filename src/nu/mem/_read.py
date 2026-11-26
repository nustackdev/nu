"""Reading a mem frame from Python code that holds a Context, not a Runtime.

Trees read a Shape's values through its refs. Bracket code in Python, which
gets a Context, reads them with :func:`read` instead of reaching into the
dict the frame binds.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang.null import NULL


if TYPE_CHECKING:
    from nu.domains.shape import Shape
    from nu.lang.runtime import Context


__all__ = ["read"]


def read(ctx: Context, shape: type[Shape], slot: str, default: object = NULL) -> object:
    """The value ``slot`` of ``shape`` holds on ``ctx``, or ``default``.

    Reads the nearest frame bound for ``shape``, in one lookup. ``default``
    when no frame for ``shape`` is in scope or the slot holds nothing. The
    value is the stored one, as a frame holds it.
    """
    try:
        data = ctx.get(dict, shape)
    except LookupError:
        return default
    return data.get(slot, default)
