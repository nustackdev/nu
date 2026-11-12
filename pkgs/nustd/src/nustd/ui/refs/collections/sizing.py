"""Height and scroll on a container, and grow / basis for one child of a Row or Column.

A container sizes to what it holds unless it says otherwise. Three props say
otherwise, the same on every container that takes them (Column, Row, Grid,
Box):

- ``height``: the container is that tall, whatever it holds.
- ``max_height``: it grows with what it holds up to that, no further.
- ``scroll``: what happens to content past the edge: ``"y"`` scrolls it
  down, ``"x"`` across, ``"both"`` either way, ``"none"`` (the default) lets
  it show. A scrolling container with no height of its own scrolls once
  whatever holds it runs out of room.

A length is an int (px) or a CSS length as text: ``"60vh"``, ``"20rem"``,
``"100%"``. They ship only when set, so a container that says nothing sends
nothing new.

``grow`` and ``basis`` belong to the Row or Column, keyed by the child, as a
Grid's ``spans`` are: the child carries nothing. ``grow={"main": 2}`` gives
that child twice the free room a plain fill child gets; ``basis={"side": 280}``
makes that child 280px along the line before any growing.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

from nustd.ui.core import check_key


if TYPE_CHECKING:
    from collections.abc import Mapping


__all__ = ["Length", "Scroll", "normalize_length", "normalize_weights", "sizing_props"]


Scroll = Literal["none", "y", "x", "both"]

#: A size as written: px as an int, or a CSS length as text.
Length = int | str

_SCROLLS = ("none", "y", "x", "both")
_LENGTH = re.compile(r"^\d+(\.\d+)?(px|rem|em|%|vh|vw|dvh|svh|lvh|ch)$")


def normalize_length(owner: str, name: str, value: Length | None) -> int | str | None:
    """``value`` as the wire carries it: px as an int, a CSS length as text, None unset."""
    if value is None:
        return None
    if isinstance(value, bool):
        msg = f"{owner} {name} is px or a CSS length, not {value!r}"
        raise TypeError(msg)
    if isinstance(value, int | float):
        px = int(value)
        if px < 0:
            msg = f"{owner} {name} must be >= 0 px, not {value}"
            raise ValueError(msg)
        return px
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
        if not _LENGTH.match(text):
            msg = f"{owner} {name} is px or a CSS length (60vh, 20rem, 100%), not {value!r}"
            raise ValueError(msg)
        return text
    msg = f"{owner} {name} is px or a CSS length, not {type(value).__name__} {value!r}"
    raise TypeError(msg)


def sizing_props(
    owner: str,
    *,
    height: Length | None = None,
    max_height: Length | None = None,
    scroll: Scroll = "none",
) -> dict[str, object]:
    """The sizing props that are set, ready to merge into a slot's props."""
    if scroll not in _SCROLLS:
        msg = f"{owner} scroll is one of {', '.join(_SCROLLS)}, not {scroll!r}"
        raise ValueError(msg)
    out: dict[str, object] = {}
    h = normalize_length(owner, "height", height)
    if h is not None:
        out["height"] = h
    mh = normalize_length(owner, "max_height", max_height)
    if mh is not None:
        out["max_height"] = mh
    if scroll != "none":
        out["scroll"] = scroll
    return out


def normalize_weights(
    owner: str, name: str, weights: Mapping[int | str, int] | None
) -> dict[str, int]:
    """A per child map (``grow`` / ``basis``) keyed as the wire keys children.

    A key is the child's position (int) or name (str), checked the way the
    container's own descent checks it.
    """
    out: dict[str, int] = {}
    for key, value in (weights or {}).items():
        check_key(owner, key)
        if isinstance(value, bool) or not isinstance(value, int | float):
            msg = f"{owner} {name} of {key!r} is a number, not {value!r}"
            raise TypeError(msg)
        n = int(value)
        if n < 0:
            msg = f"{owner} {name} of {key!r} must be >= 0, not {value}"
            raise ValueError(msg)
        out[str(key)] = n
    return out
