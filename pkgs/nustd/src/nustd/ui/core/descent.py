"""Descent: the child a container answers with at a place.

Every container picks its own way down (``row[0]``, ``card.actions``,
``field.control``, ``tabs["overview"]``); each one ends here. The child at a
place is built from a spec when the container knows its kind (an ``item=``
default, a named part's default) and is a bare ``ItemRef`` when it does not.
A bare child names no kind on the wire: it can erase, hide or display what is
there, and ``.to(Kind)`` names the kind at the same place so the chain goes on.

Keys: an ``int`` is a position, a ``str`` is a name. Both ship as the same
text segment, so where a container takes both, a name that reads as a number
(``"0"``) would land on the position ``0``; it is refused there rather than
left to collide. A computed key (a term) is taken as given.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.shape import Slot
from nu.lang import Nu

from .base import ItemRef, Ref
from .section import Section


if TYPE_CHECKING:
    from collections.abc import Collection


__all__ = ["as_spec", "check_key", "child_at"]


def as_spec(owner: str, spec: object) -> Slot | None:
    """``spec`` as a ``Slot``: a ui ref class, a Section class, or ``Kind.slot(...)``.

    A class becomes its own ``slot()`` with the defaults it declares, the way
    a declared slot ships them. None stays None (no default kind).
    """
    if spec is None or isinstance(spec, Slot):
        if isinstance(spec, Slot) and not (
            isinstance(spec.ref_cls, type) and issubclass(spec.ref_cls, Ref)
        ):
            msg = f"{owner} item must be a ui kind, not a slot of {spec.ref_cls!r}"
            raise TypeError(msg)
        return spec
    if isinstance(spec, type) and issubclass(spec, (Section, Ref)) and spec is not Section:
        return spec.slot()  # type: ignore[return-value]
    msg = (
        f"{owner} item must be a ref class, a Section class or a Kind.slot(...) spec, not {spec!r}"
    )
    raise TypeError(msg)


def check_key(
    owner: str,
    key: object,
    *,
    positions: bool = True,
    names: bool = True,
    parts: Collection[str] = (),
) -> object:
    """``key`` if ``owner`` takes it, else raise. ``parts`` are names reached by property.

    Raises:
        TypeError: a key of a kind ``owner`` does not take (None, a bool, a
            tuple, a float, an int where only names go, ...).
        IndexError: a negative position: there is no length to count back from.
        ValueError: an empty name, a name that reads as a position, or a name
            that is one of ``owner``'s own parts.
    """
    if isinstance(key, Nu):
        return key
    if isinstance(key, bool) or key is None:
        msg = f"{owner} takes no {key!r} key; use an int position or a str name"
        raise TypeError(msg)
    if isinstance(key, int):
        if not positions:
            msg = f"{owner} children are reached by name, not by position: {owner}[{key!r}]"
            raise TypeError(msg)
        if key < 0:
            msg = f"{owner} has no length to count back from; use a position >= 0, not {key}"
            raise IndexError(msg)
        return key
    if isinstance(key, str):
        if not names:
            msg = f"{owner} children are reached by position, not by name: {owner}[{key!r}]"
            raise TypeError(msg)
        if not key:
            msg = f"{owner} takes no empty name"
            raise ValueError(msg)
        if positions and key.isdigit():
            msg = (
                f"{owner}[{key!r}]: a name that reads as a number lands on that position;"
                f" use the int {int(key)} for a position, or a name that is not a number"
            )
            raise ValueError(msg)
        if key in parts:
            msg = f"{owner}[{key!r}] is the container's own part; reach it as .{key}"
            raise ValueError(msg)
        return key
    kinds = " or ".join(
        k for k, on in (("an int position", positions), ("a str name", names)) if on
    )
    msg = f"{owner} keys are {kinds}, not {type(key).__name__} {key!r}"
    raise TypeError(msg)


def child_at(parent: Ref, key: object, spec: Slot | None = None) -> ItemRef:
    """The child of ``parent`` at ``key``: built from ``spec``, or bare when there is none."""
    section_cls = parent._payload.get("section_cls")
    if spec is None:
        return ItemRef(key, parent_ref=parent, owner_shape=section_cls)
    return spec.create_ref(owner_shape=section_cls, parent_ref=parent, address=key)  # type: ignore[return-value]
