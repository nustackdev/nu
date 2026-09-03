"""Assemble interaction records. Assumes the guide, degrades without it.

Nothing is parsed here. The two sources are read by
:mod:`nu.info.core.docstring` and :mod:`nu.info.core.source`, merged where
they must be by :mod:`nu.info.core.contract`, and this only decides which of
those facts an interaction record holds.

A missing section is an empty field, not an error, so the assembler can run
over a package mid-pass and report what is there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.info.core.contract import YIELDS, call_form
from nu.info.core.docstring import split_docstring
from nu.info.core.source import public_members
from nu.info.record import prose
from nu.lang import kinds
from nu.lang.kinds import Interaction

from .record import InteractionRecord


if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    "catalogue",
    "parse_interaction",
]

# The kinds.py classes an atom can be an instance of, most specific first.
_KIND_CLASSES = tuple(
    getattr(kinds, name) for name in kinds.__all__ if isinstance(getattr(kinds, name), type)
)


def parse_interaction(atom: type, path: str = "") -> InteractionRecord:
    """One interaction record for ``atom``."""
    blocks = split_docstring(atom.__doc__)
    return InteractionRecord(
        **prose(atom, atom.__name__, path or f"{atom.__module__}.{atom.__name__}", blocks),
        args=call_form(atom, blocks),
        yields=blocks.text_of(*YIELDS),
        kind=_kind(atom),
        sort=_declared(atom, "sort"),
        cardinality=_declared(atom, "cardinality"),
    )


def catalogue(module: ModuleType) -> tuple[InteractionRecord, ...]:
    """A record per interaction the module exports, in export order."""
    name = module.__name__
    return tuple(
        parse_interaction(member.target, path=f"{name}.{member.name}")
        for member in public_members(module)
        if isinstance(member.target, type) and issubclass(member.target, Interaction)
    )


def _kind(atom: type) -> str:
    """The name of the most specific ``nu.lang.kinds`` class ``atom`` is."""
    for base in atom.__mro__:
        if base in _KIND_CLASSES:
            return base.__name__
    return ""


def _declared(atom: type, name: str) -> str:
    """A declared engine attribute, as text."""
    attribute = getattr(atom, "_attributes", {}).get(name)
    if attribute is None:
        return ""
    value = getattr(attribute, "value", None)
    return getattr(value, "value", None) or str(value)
