"""The form kind: record, parse, verify.

A Form is a typed interface: the operator surface a value carries. ``Int``
is a Form over ``int``, ``Str`` over ``str``. Every Form is a builder, so
FormRecord is a builder record; the kind exists so a catalogue can carry
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
from nu.lang import Form
from nu.lang.kinds import Ref


if TYPE_CHECKING:
    from types import ModuleType

    from nu.info.core.contract import Violation


__all__ = [
    "FormRecord",
    "catalogue",
    "parse_form",
    "verify_form",
]


@dataclass(frozen=True)
class FormRecord(BuilderRecord):
    """One Form class: the builder shape, tagged as a Form for dispatch."""


def parse_form(cls: type, path: str = "") -> FormRecord:
    """One FormRecord for ``cls``."""
    blocks = split_docstring(cls.__doc__)
    return FormRecord(
        **prose(cls, cls.__name__, path or f"{cls.__module__}.{cls.__name__}", blocks),
        methods=resolve_methods(cls),
    )


def catalogue(module: ModuleType) -> tuple[FormRecord, ...]:
    """A FormRecord per Form subclass the module exports, in export order."""
    name = module.__name__
    return tuple(
        parse_form(member.target, path=f"{name}.{member.name}")
        for member in public_members(module)
        if isinstance(member.target, type) and _is_form(member.target)
    )


def verify_form(cls: type) -> list[Violation]:
    """Every way ``cls`` lies about the format. No form-specific laws yet."""
    return verify_builder(cls)


def _is_form(cls: type) -> bool:
    if cls is Form:
        return False
    return issubclass(cls, Form) and not issubclass(cls, Ref)
