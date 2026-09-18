"""The service kind: record, parse, verify.

A Service is the flat sibling of a Shape: a class of declared methods, never
instantiated, whose attribute access hands out MethodRefs. Where a Shape says
what an app's state looks like, a Service says what it can call out to. Like
a Shape it belongs to whoever wrote the app, not to nu.

The record is prose plus a flat list of entries, one per method, and stops
there. ``entry.parse_entry`` resolves one of them to the MethodRef class's
own RefRecord - the declaration's config (the endpoint path, the verb) rides
on the entry, since it exists per method and nowhere on the Ref class.


The docstring contract for a Service
------------------------------------

The same as a Shape's, for the same reason, and it is worth stating twice
because it is the half of the format people get wrong by habit:

- **Methods are not written.** They are on ``_methods``, with their ref class
  and their full declaration config. Listing them in prose duplicates data
  that is already exact.
- **Args and Yields are violations.** A Service is never called; the *methods*
  are. What a method takes and yields is written on the MethodRef class that
  declares it, which is where a reader lands one lookup later.
- Summary, description and notes are the writable surface. Notes is where the
  facts that exist nowhere else go: which fabric the Service must be bound
  under, what authentication the endpoints assume, which calls are not
  idempotent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.inspect.core.contract import (
    ARGS,
    YIELDS,
    Violation,
    check_absent,
    check_example,
    check_summary,
)
from nu.inspect.core.docstring import split_docstring
from nu.inspect.core.source import public_members
from nu.inspect.entry import Entry, entries_of, is_service
from nu.inspect.record import Record, prose


if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    "ServiceRecord",
    "catalogue",
    "parse_service",
    "verify_service",
]


@dataclass(frozen=True)
class ServiceRecord(Record):
    """One Service class: the prose, plus one flat entry per method."""

    entries: tuple[Entry, ...] = ()


def parse_service(cls: type, path: str = "", *, aliases: tuple[str, ...] = ()) -> ServiceRecord:
    """One ServiceRecord for ``cls``. Methods are listed, not expanded."""
    blocks = split_docstring(cls.__doc__)
    where = path or f"{cls.__module__}.{cls.__name__}"
    return ServiceRecord(
        **prose(cls, cls.__name__, where, blocks, aliases=aliases),
        entries=entries_of(cls, where),
    )


def catalogue(module: ModuleType) -> tuple[ServiceRecord, ...]:
    """A ServiceRecord per Service the module declares, in export order.

    Same standing as the Shape catalogue: not the entry point, but the answer
    to what is in this app module.
    """
    name = module.__name__
    return tuple(
        parse_service(  # type: ignore[arg-type]
            member.target, path=f"{name}.{member.name}", aliases=member.aliases
        )
        for member in public_members(module)
        if is_service(member.target)
    )


def verify_service(cls: type) -> list[Violation]:
    """Every way ``cls`` lies about the format. Same two removals as a Shape."""
    name = cls.__name__
    blocks = split_docstring(cls.__doc__)
    violations = check_summary(name, blocks)
    violations.extend(check_absent(name, blocks, *ARGS, rule="args-not-callable"))
    violations.extend(check_absent(name, blocks, *YIELDS, rule="yields-not-a-term"))
    violations.extend(check_example(name, blocks))
    return violations
