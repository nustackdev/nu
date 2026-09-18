"""Module enumeration: a module in, its public members out. No Nu knowledge.

One rule, in order: use ``__all__`` when the module declares one, otherwise
take the public names whose ``__module__`` is this module (which drops
re-exports and anything a ``TYPE_CHECKING`` block pulled in). Either way the
result is deduped by object identity, so a member exported under two names is
reported once, under the first name seen.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType


__all__ = [
    "Member",
    "public_members",
]


@dataclass(frozen=True)
class Member:
    """One public member of a module, with the names it is exported under."""

    name: str
    target: object
    aliases: tuple[str, ...] = ()


def public_members(module: ModuleType) -> tuple[Member, ...]:
    """The module's public members, deduped by object identity."""
    seen: dict[int, list[str]] = {}
    order: list[tuple[int, object]] = []
    for name in _names(module):
        target = getattr(module, name, None)
        if target is None or isinstance(target, ModuleType):
            continue
        key = id(target)
        if key in seen:
            seen[key].append(name)
            continue
        seen[key] = [name]
        order.append((key, target))
    return tuple(
        Member(name=seen[key][0], target=target, aliases=tuple(seen[key][1:]))
        for key, target in order
    )


def _names(module: ModuleType) -> tuple[str, ...]:
    """Exported names, from ``__all__`` when declared, else own public names."""
    declared = getattr(module, "__all__", None)
    if declared is not None:
        return tuple(declared)
    own = getattr(module, "__name__", "")
    return tuple(
        name
        for name in vars(module)
        if not name.startswith("_") and getattr(getattr(module, name), "__module__", "") == own
    )
