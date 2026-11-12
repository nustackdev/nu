"""Container layout: four layers, the same words on every container.

- **size**: ``width``, ``min_width``, ``max_width``, ``height``, ``min_height``,
  ``max_height``, each a ``Length``; ``scroll`` (``"y"``, ``"x"``, ``"both"``)
  for content past the edge. A scrolling container with no height of its own
  scrolls once whatever holds it runs out of room. On a titled surface the
  body scrolls and the title stays put.
- **space**: ``padding`` and ``gap``, one int scale from 0 to 16, a step is
  4px (``gap=3`` is 12px).
- **arrange**: ``justify`` places children along the main axis (the way they
  flow), ``align`` across it. Row flows right, so its ``justify`` is
  horizontal; Column flows down, so its ``justify`` is vertical.
- **surface**: ``variant`` and ``size`` on Card and PageSection, their own
  props (see each).

Each family adds its own props beside the layers (Row ``wrap`` and
``stack_below``, Grid ``cols``, ``rows``, ``max_columns``, ``min_cell_width``,
``dense``, a Card's ``variant`` and ``size``): a container declares them in
``_family``, name to check, and they go through the same check path.

A ``Length`` is an int (px), a CSS length as text (``"60vh"``, ``"20rem"``,
``"100%"``) or a named page width (``"form"`` 480, ``"prose"`` 640, ``"panel"``
960, ``"main"`` 1200, ``"dashboard"`` 1400, ``"full"`` no cap). It is checked
where it is written.

A prop ships only when it is set: unset, the browser draws the container's
own look (Card's gap 3, Container's gutter, Row's center). So a container
that says nothing sends nothing.

**Per child.** A child never lays itself out: the parent keeps a map per idea,
keyed by the key the child is reached by (``row["main"]`` is keyed
``"main"``, a placed grid cell ``grid[1, 0]`` is keyed ``(1, 0)``). Keys stay
with a child through ``move``, so its layout follows it. Five maps, no more:

- ``grow``: share of the spare room, a true ratio: ``{"a": 1, "b": 2}`` draws
  1:2. A grown child starts from 0 (or from its ``basis``).
- ``basis``: the size along the flow before any growing, a ``Length``.
- ``span``: tracks a grid cell covers: an int is columns, ``{"cols": 2,
  "rows": 3}`` both. A tuple is refused, its order is a trap.
- ``align_self``: ``align`` for one child.
- ``sticky``: the edge a child sticks to while the container scrolls,
  ``{"head": "top"}``.

Two doors at run time, one per idea: ``set_layout(**props)`` changes the
container's own props (every name its ``slot()`` takes for layers, family
and surface), ``set_child(key, grow=, basis=, span=, align_self=, sticky=)``
one child's entries. What either leaves out stays, ``None`` drops it.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Literal, TypedDict

from nu.forms import Dict
from nu.lang import Nu
from nu.lang.sentinels import UNSET
from nustd.ui.core import Ref, Send, Write


__all__ = [
    "SIZE",
    "ArrangeLayout",
    "Justify",
    "Length",
    "Scroll",
    "SetChild",
    "SizeLayout",
    "SpaceLayout",
    "Span",
    "StackLayout",
    "Sticky",
    "choice",
    "flag",
    "layout_props",
    "normalize_length",
    "px",
]


#: A size as written: px as an int, a CSS length as text, or a page width name.
Length = int | str

#: Content past the edge: scroll it down, across, or either way.
Scroll = Literal["y", "x", "both"]

#: Where children sit along the main axis.
Justify = Literal["start", "center", "end", "between"]

#: Where children sit across the main axis.
Align = Literal["start", "center", "end", "stretch", "baseline"]

#: The edge a child sticks to while its container scrolls.
Sticky = Literal["top", "bottom", "left", "right"]

#: Tracks a grid cell covers: columns, or ``{"cols": c, "rows": r}``.
Span = int | Mapping[str, int]

#: How a family prop is checked: ``(owner, name, value)`` to the wire value.
Check = Callable[[str, str, object], object]

#: Named page widths, the kit's ``--container-*`` tokens.
PAGE_WIDTHS = ("form", "prose", "panel", "main", "dashboard", "full")

SIZE = frozenset(
    {"width", "min_width", "max_width", "height", "min_height", "max_height", "scroll"}
)
SPACE = frozenset({"padding", "gap"})
ARRANGE = frozenset({"justify", "align"})

#: The per child maps, by name.
CHILD_MAPS = ("grow", "basis", "span", "align_self", "sticky")

_SCROLLS = ("y", "x", "both")
_LENGTH = re.compile(r"^\d+(\.\d+)?(px|rem|em|%|vh|vw|dvh|svh|lvh|ch)$")
_SPACE_MAX = 16


class SizeLayout(TypedDict, total=False):
    """The size layer, every container."""

    width: Length
    min_width: Length
    max_width: Length
    height: Length
    min_height: Length
    max_height: Length
    scroll: Scroll


class SpaceLayout(SizeLayout, total=False):
    """Size and space."""

    padding: int
    gap: int


class ArrangeLayout(SpaceLayout, total=False):
    """Size, space and arrange."""

    justify: str
    align: str


class StackLayout(ArrangeLayout, total=False):
    """Every layer, a hairline between children, and the flow's per child maps."""

    divided: bool
    grow: Mapping[object, float]
    basis: Mapping[object, Length]
    align_self: Mapping[object, str]
    sticky: Mapping[object, Sticky]


# ---- values ----------------------------------------------------------------


def normalize_length(owner: str, name: str, value: object) -> int | str:
    """``value`` as the wire carries it: px as an int, CSS length or page width as text."""
    if isinstance(value, bool):
        msg = f"{owner} {name} is a length (px, CSS text or a page width), not {value!r}"
        raise TypeError(msg)
    if isinstance(value, int | float):
        if value < 0:
            msg = f"{owner} {name} must be >= 0 px, not {value}"
            raise ValueError(msg)
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
        if text in PAGE_WIDTHS or _LENGTH.match(text):
            return text
        msg = (
            f"{owner} {name} is px, a CSS length (60vh, 20rem, 100%) or a page width"
            f" ({', '.join(PAGE_WIDTHS)}), not {value!r}"
        )
        raise ValueError(msg)
    msg = f"{owner} {name} is a length, not {type(value).__name__} {value!r}"
    raise TypeError(msg)


def normalize_space(owner: str, name: str, value: object) -> int:
    """A ``padding`` or ``gap`` step: an int from 0 to 16, a step is 4px."""
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{owner} {name} is a step from 0 to {_SPACE_MAX} (4px each), not {value!r}"
        raise TypeError(msg)
    if not 0 <= value <= _SPACE_MAX:
        msg = f"{owner} {name} is a step from 0 to {_SPACE_MAX} (4px each), not {value}"
        raise ValueError(msg)
    return value


def one_of(owner: str, name: str, value: object, choices: tuple[str, ...]) -> str:
    """``value`` when it is one of ``choices``, else fail loud with the list."""
    if value not in choices:
        msg = f"{owner} {name} is one of {', '.join(choices)}, not {value!r}"
        raise ValueError(msg)
    return value  # type: ignore[return-value]


def px(owner: str, name: str, value: object) -> int:
    """A width in px, an int >= 0, for the props that compare against one."""
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{owner} {name} is a width in px (int), not {value!r}"
        raise TypeError(msg)
    if value < 0:
        msg = f"{owner} {name} must be >= 0 px, not {value}"
        raise ValueError(msg)
    return value


def flag(owner: str, name: str, value: object) -> bool:
    """A family switch: True or False."""
    if not isinstance(value, bool):
        msg = f"{owner} {name} is True or False, not {value!r}"
        raise TypeError(msg)
    return value


def choice(*words: str) -> Check:
    """A check that takes one of ``words``."""

    def check(owner: str, name: str, value: object) -> str:
        return one_of(owner, name, value, words)

    return check


def normalize_span(owner: str, key: object, value: object) -> dict[str, int]:
    """A span as the wire carries it, ``{"cols": c, "rows": r}``."""
    if isinstance(value, bool):
        msg = f"{owner} span of {key!r} is columns (int) or {{'cols', 'rows'}}, not {value!r}"
        raise TypeError(msg)
    if isinstance(value, int):
        cols, rows = value, 1
    elif isinstance(value, Mapping):
        extra = set(value) - {"cols", "rows"}
        if extra:
            msg = f"{owner} span of {key!r} takes cols and rows, not {', '.join(sorted(extra))}"
            raise ValueError(msg)
        cols, rows = value.get("cols", 1), value.get("rows", 1)
        if any(isinstance(n, bool) or not isinstance(n, int) for n in (cols, rows)):
            msg = f"{owner} span of {key!r}: cols and rows are ints, not {dict(value)!r}"
            raise TypeError(msg)
    else:
        msg = (
            f"{owner} span of {key!r} is columns (int) or {{'cols': c, 'rows': r}},"
            f" not {type(value).__name__} {value!r}"
        )
        raise TypeError(msg)
    if cols < 1 or rows < 1:
        msg = f"{owner} span of {key!r} is at least 1 by 1, not {cols} by {rows}"
        raise ValueError(msg)
    return {"cols": cols, "rows": rows}


def _grow(owner: str, key: object, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"{owner} grow of {key!r} is a number, not {value!r}"
        raise TypeError(msg)
    if value < 0:
        msg = f"{owner} grow of {key!r} must be >= 0, not {value}"
        raise ValueError(msg)
    return value


def child_value(cls: type, name: str, key: object, value: object) -> object:
    """One entry of the per child map ``name``, checked for container ``cls``."""
    owner = cls.__name__
    if name == "grow":
        return _grow(owner, key, value)
    if name == "basis":
        return normalize_length(owner, f"basis of {key!r}", value)
    if name == "span":
        return normalize_span(owner, key, value)
    if name == "align_self":
        return one_of(owner, f"align_self of {key!r}", value, cls._self_aligns)  # type: ignore[attr-defined]
    return one_of(owner, f"sticky of {key!r}", value, cls._sticky_sides)  # type: ignore[attr-defined]


# ---- the props a slot ships --------------------------------------------------


def layout_props(cls: type, given: Mapping[str, object], **context: object) -> dict[str, object]:
    """The layout props of container ``cls`` that are set, checked, as the wire carries them.

    ``cls`` names what it takes: ``_layout`` (its layer props and
    ``divided``), ``_family`` (its family and surface props, each with its
    check), ``_children`` (its per child maps), ``_aligns``,
    ``_justifies``, ``_self_aligns`` and ``_sticky_sides``. A name it does not
    take fails loud with the list it does. ``context`` reaches the
    container's ``_child_key`` (a grid passes whether it is placed).
    """
    owner = cls.__name__
    family: Mapping[str, Check] = cls._family  # type: ignore[attr-defined]
    takes = cls._layout | frozenset(family) | frozenset(cls._children)  # type: ignore[attr-defined]
    unknown = sorted(set(given) - takes)
    if unknown:
        msg = (
            f"{owner} takes no {', '.join(unknown)}; its layout props are"
            f" {', '.join(sorted(takes))}"
        )
        raise TypeError(msg)
    out: dict[str, object] = {}
    for name, value in given.items():
        if value is None:
            continue
        if name in family:
            out[name] = family[name](owner, name, value)
        elif name in SIZE:
            if name == "scroll":
                out[name] = one_of(owner, name, value, _SCROLLS)
            else:
                out[name] = normalize_length(owner, name, value)
        elif name in SPACE:
            out[name] = normalize_space(owner, name, value)
        elif name == "justify":
            out[name] = one_of(owner, name, value, cls._justifies)  # type: ignore[attr-defined]
        elif name == "align":
            out[name] = one_of(owner, name, value, cls._aligns)  # type: ignore[attr-defined]
        elif name in CHILD_MAPS:
            entries = child_map(cls, name, value, **context)
            if entries:
                out[name] = entries
        elif isinstance(value, bool):
            out[name] = value
        else:
            msg = f"{owner} {name} is True or False, not {value!r}"
            raise TypeError(msg)
    return out


def child_map(cls: type, name: str, value: object, **context: object) -> dict[str, object]:
    """A per child map as the wire keys it: each child's key as text, each value checked."""
    owner = cls.__name__
    if not isinstance(value, Mapping):
        msg = f"{owner} {name} maps a child's key to its value, not {value!r}"
        raise TypeError(msg)
    out: dict[str, object] = {}
    for key, v in value.items():
        entry = child_value(cls, name, key, v)
        if name == "span" and entry == {"cols": 1, "rows": 1}:
            continue
        out[cls._child_key(key, **context)] = entry  # type: ignore[attr-defined]
    return out


# ---- run time ----------------------------------------------------------------


class SetChild(Send):
    """Change one child's entries in its parent's per child maps.

    Payload ``{key, grow?, basis?, span?, align_self?, sticky?}``: a name
    left out keeps its entry, ``None`` drops it, a 1 by 1 span drops too.
    """

    def _frame_payload(self, values: list[object]) -> object:
        key, changes = values
        return {"key": str(key), **changes}  # type: ignore[dict-item]


class ChildLayout:
    """``set_child`` for a container that keeps per child maps."""

    def set_child(
        self,
        child: object,
        *,
        grow: float | None = UNSET,  # type: ignore[assignment]
        basis: Length | None = UNSET,  # type: ignore[assignment]
        span: Span | None = UNSET,  # type: ignore[assignment]
        align_self: str | None = UNSET,  # type: ignore[assignment]
        sticky: Sticky | None = UNSET,  # type: ignore[assignment]
    ) -> Nu:
        """Change how the parent lays one child out; left out stays, ``None`` drops.

        ``child`` is the child's key, ``(r, c)`` for a placed grid cell or a
        table cell, or the child itself (``row["k"]``, ``t[0, 1]``), read for
        its key. A child of another container is refused.
        """
        cls = type(self)
        owner = self._owner_name()  # type: ignore[attr-defined]
        given = {
            "grow": grow,
            "basis": basis,
            "span": span,
            "align_self": align_self,
            "sticky": sticky,
        }
        changes: dict[str, object] = {}
        for name, value in given.items():
            if value is UNSET:
                continue
            if name not in cls._children:  # type: ignore[attr-defined]
                msg = (
                    f"{owner} keeps no {name} per child; it keeps"
                    f" {', '.join(cls._children) or 'none'}"  # type: ignore[attr-defined]
                )
                raise TypeError(msg)
            if value is None or isinstance(value, Nu):
                changes[name] = value
                continue
            entry = child_value(cls, name, child, value)
            changes[name] = None if entry == {"cols": 1, "rows": 1} else entry
        if not changes:
            msg = f"{owner}.set_child changes nothing; give grow, basis, span, align_self or sticky"
            raise TypeError(msg)
        if isinstance(child, Ref):
            key: object = self._key_of_child(child)  # type: ignore[attr-defined]
        else:
            key = self._child_runtime_key(child)  # type: ignore[attr-defined]
        return SetChild(self, key, Dict.of(**changes))


def same_place(a: object, b: object) -> bool:
    """Whether two refs name one place: same kinds and segments all the way up."""
    while a is not None and b is not None:
        if a is b:
            return True
        if type(a) is not type(b):
            return False
        sa, sb = a._payload.get("segment"), b._payload.get("segment")  # type: ignore[attr-defined]
        if isinstance(sa, Nu) or isinstance(sb, Nu):
            if sa is not sb:
                return False
        elif sa != sb:
            return False
        a, b = a._parent, b._parent  # type: ignore[attr-defined]
    return a is None and b is None


class Laid:
    """``set_layout`` for a container: change its own props at run time."""

    def set_layout(self, **props: object) -> Nu:
        """Change the container's props (``gap=2``, ``wrap=True``); left out stays, ``None`` unsets.

        Takes every name the container's ``slot()`` takes for its layers,
        its family and its surface (``cols``, ``max_columns``, ``variant``,
        ``size``...), checked the same way. A term passes as it is. A child's
        entries are ``set_child``'s.
        """
        cls = type(self)
        owner = self._owner_name()  # type: ignore[attr-defined]
        takes = cls._layout | frozenset(cls._family)  # type: ignore[attr-defined]
        unknown = sorted(set(props) - takes)
        if unknown or not props:
            msg = (
                f"{owner}.set_layout takes {', '.join(sorted(takes))}"
                f"{'; not ' + ', '.join(unknown) if unknown else ''}"
            )
            raise TypeError(msg)
        checked = layout_props(
            cls, {k: v for k, v in props.items() if v is not None and not isinstance(v, Nu)}
        )
        out: dict[str, object] = {
            k: (checked.get(k) if v is not None and not isinstance(v, Nu) else v)
            for k, v in props.items()
        }
        return Write(self, Dict.of(**out))  # type: ignore[arg-type]
