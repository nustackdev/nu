"""The builder kind: record, parse, verify.

A builder is a class that hosts calls. Every Form and every Ref is a builder,
so a BuilderRecord is what those two kinds share: the class prose plus the
MRO-resolved set of methods it exposes below ``Nu``.

``form`` and ``ref`` extend this record with what makes each specific. A raw
BuilderRecord is what you reach for when neither specialisation is at hand or
when a caller wants the two kinds in one collection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.inspect.call import CallRecord, parse_binding, verify_call
from nu.inspect.core.contract import Violation, check_example, check_summary
from nu.inspect.core.docstring import split_docstring
from nu.inspect.core.source import public_members, walk_bindings
from nu.inspect.record import Record, prose
from nu.lang import Form, Nu
from nu.lang.kinds import Ref


if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    "BuilderRecord",
    "catalogue",
    "parse_builder",
    "resolve_methods",
    "verify_builder",
]


# Declaration-time DSL entries a Ref or Service class exposes as classmethods.
# They build descriptors at class-body time, not Nu terms, and are captured
# separately by the ref/service records (or deferred to the DSL kinds later).
DSL_SKIP = frozenset({"slot", "method"})


@dataclass(frozen=True)
class BuilderRecord(Record):
    """One builder class: what it is, and every call it exposes."""

    methods: tuple[CallRecord, ...] = ()


def parse_builder(cls: type, path: str = "") -> BuilderRecord:
    """One BuilderRecord for ``cls``."""
    blocks = split_docstring(cls.__doc__)
    return BuilderRecord(
        **prose(cls, cls.__name__, path or f"{cls.__module__}.{cls.__name__}", blocks),
        methods=resolve_methods(cls),
    )


def resolve_methods(cls: type, *, skip: frozenset[str] = DSL_SKIP) -> tuple[CallRecord, ...]:
    """MRO-resolved call records for ``cls``, below ``Nu``.

    Shared by ``parse_builder`` and by the ref/form parsers so a specialised
    record still describes exactly the calls a person writes.
    """
    bindings = walk_bindings(cls, stop=Nu, skip=skip)
    return tuple(parse_binding(binding, host=cls) for binding in bindings)


def catalogue(module: ModuleType) -> tuple[BuilderRecord, ...]:
    """A record per Form or Ref subclass the module exports, in export order.

    Dispatches per class so a Ref returns a RefRecord and a Form returns a
    FormRecord; the base BuilderRecord shape is preserved for consumers that
    only read the shared fields.
    """
    from nu.inspect.form import parse_form
    from nu.inspect.ref import parse_ref

    name = module.__name__
    out: list[BuilderRecord] = []
    for member in public_members(module):
        cls = member.target
        if not isinstance(cls, type):
            continue
        path = f"{name}.{member.name}"
        if _is_ref(cls):
            out.append(parse_ref(cls, path=path))
        elif _is_form(cls):
            out.append(parse_form(cls, path=path))
    return tuple(out)


def verify_builder(cls: type) -> list[Violation]:
    """Every way ``cls`` and its methods lie about the format."""
    name = cls.__name__
    blocks = split_docstring(cls.__doc__)
    violations = check_summary(name, blocks)
    violations.extend(check_example(name, blocks))
    for binding in walk_bindings(cls, stop=Nu, skip=DSL_SKIP):
        subject = f"{name}.{binding.name}"
        violations.extend(verify_call(binding.target, subject=subject))
    return violations


def _is_form(cls: type) -> bool:
    if cls is Form:
        return False
    return issubclass(cls, Form) and not issubclass(cls, Ref)


def _is_ref(cls: type) -> bool:
    if cls is Ref:
        return False
    return issubclass(cls, Ref)
