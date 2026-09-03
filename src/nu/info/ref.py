"""The ref kind: record, parse, verify.

A Ref names an addressed slot in a Fabric. Every Ref is a builder, so
RefRecord is a builder record; the kind exists so a catalogue can carry
Forms and Refs alongside each other and a consumer can dispatch on the
record's type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.info.builder import BuilderRecord, resolve_methods, verify_builder
from nu.info.core.docstring import split_docstring
from nu.info.core.source import public_members
from nu.info.record import prose
from nu.lang.kinds import Ref


if TYPE_CHECKING:
    from types import ModuleType

    from nu.info.core.contract import Violation


__all__ = [
    "RefRecord",
    "catalogue",
    "parse_ref",
    "verify_ref",
]


@dataclass(frozen=True)
class RefRecord(BuilderRecord):
    """One Ref class: the builder shape, tagged as a Ref for dispatch."""


def parse_ref(cls: type, path: str = "") -> RefRecord:
    """One RefRecord for ``cls``."""
    blocks = split_docstring(cls.__doc__)
    return RefRecord(
        **prose(cls, cls.__name__, path or f"{cls.__module__}.{cls.__name__}", blocks),
        methods=resolve_methods(cls),
    )


def catalogue(module: ModuleType) -> tuple[RefRecord, ...]:
    """A RefRecord per Ref subclass the module exports, in export order."""
    name = module.__name__
    return tuple(
        parse_ref(member.target, path=f"{name}.{member.name}")
        for member in public_members(module)
        if isinstance(member.target, type) and _is_ref(member.target)
    )


def verify_ref(cls: type) -> list[Violation]:
    """Every way ``cls`` lies about the format. No ref-specific laws yet."""
    return verify_builder(cls)


def _is_ref(cls: type) -> bool:
    if cls is Ref:
        return False
    return issubclass(cls, Ref)
