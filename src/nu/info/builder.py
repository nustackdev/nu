"""The builder kind: record, parse, verify.

A builder is a class that hosts calls: a Form or a Ref. It is not a term
itself in this iteration; the ``__init__``-as-atom side is deferred. What a
builder record carries is the full MRO-resolved set of calls its subjects
inherit from below ``Nu``, flat and self-sufficient.

Form and Ref both produce a BuilderRecord here. When their differences earn
their own fields (Ref's substrate and address, later), they get subclasses of
BuilderRecord and this file grows a sibling parser for each.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.info.call import CallRecord, parse_binding, verify_call
from nu.info.core.contract import Violation, check_example, check_summary
from nu.info.core.docstring import split_docstring
from nu.info.core.source import public_members, walk_bindings
from nu.info.record import Record, prose
from nu.lang import Form, Nu
from nu.lang.kinds import Ref


if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    "BuilderRecord",
    "catalogue",
    "parse_builder",
    "verify_builder",
]


# Declaration-time DSL entries a Ref or Service class exposes as classmethods.
# They build descriptors at class-body time, not Nu terms, and belong to the
# DSL kinds when those land.
_DSL_SKIP = frozenset({"slot", "method"})


@dataclass(frozen=True)
class BuilderRecord(Record):
    """One builder class: what it is, and every call it exposes."""

    methods: tuple[CallRecord, ...] = ()


def parse_builder(cls: type, path: str = "") -> BuilderRecord:
    """One BuilderRecord for ``cls``."""
    blocks = split_docstring(cls.__doc__)
    bindings = walk_bindings(cls, stop=Nu, skip=_DSL_SKIP)
    methods = tuple(parse_binding(binding, host=cls) for binding in bindings)
    return BuilderRecord(
        **prose(cls, cls.__name__, path or f"{cls.__module__}.{cls.__name__}", blocks),
        methods=methods,
    )


def catalogue(module: ModuleType) -> tuple[BuilderRecord, ...]:
    """A record per Form or Ref subclass the module exports, in export order."""
    name = module.__name__
    return tuple(
        parse_builder(member.target, path=f"{name}.{member.name}")
        for member in public_members(module)
        if isinstance(member.target, type) and _is_builder(member.target)
    )


def verify_builder(cls: type) -> list[Violation]:
    """Every way ``cls`` and its methods lie about the format."""
    name = cls.__name__
    blocks = split_docstring(cls.__doc__)
    violations = check_summary(name, blocks)
    violations.extend(check_example(name, blocks))
    for binding in walk_bindings(cls, stop=Nu, skip=_DSL_SKIP):
        subject = f"{name}.{binding.name}"
        violations.extend(verify_call(binding.target, subject=subject))
    return violations


def _is_builder(cls: type) -> bool:
    if not isinstance(cls, type):
        return False
    if cls is Form or cls is Ref:
        return False
    return issubclass(cls, (Form, Ref))
