"""The shape kind: record, parse, verify.

A Shape is a declared structure: a class of slots, never instantiated, whose
attribute access hands out Refs. It is the one kind nu does not export. Every
Shape belongs to whoever wrote the app, which is exactly why it is here: an
agent handed a bound app has to ask what this Shape is before it can write a
line of Nu against it.

The record is prose plus a flat list of entries, one per slot, and stops
there. ``entry.parse_entry`` is the next step down. See ``nu.inspect.entry``
for why the descent is not a tree.


The docstring contract for a Shape
----------------------------------

The rule is the same one the format is built on - write only the facts that
cannot be read off the code - and this is the first kind where it *removes* a
requirement instead of adding one.

- **Slots are not written.** Every slot is on ``_slots``: its name, its ref
  class, its declared type, its config. A docstring that lists them is
  duplicating derivable data, and the duplicate is the copy that goes stale.
  This is the inverse of an interaction, where Args is required precisely
  because a variadic constructor puts the arity nowhere else.
- **Args is a violation.** A Shape is never called and never instantiated, so
  an Args section is not a wording mistake, it is a claim about a call that
  does not exist.
- **Yields is a violation**, for the same reason: a Shape is not a term and
  does not evaluate. What a *slot* yields belongs to that slot's ref class.
- Summary, description and notes are the whole writable surface. Notes is
  where a Shape earns its docstring: which fabric it is meant to be bound
  under, which slots are written by whom, what invariant holds across slots.
  None of that is on ``_slots``.
- Example is allowed but rarely doctestable, since a Shape needs a live
  context to do anything; a plain snippet is fine.
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
from nu.inspect.entry import Entry, entries_of, is_shape
from nu.inspect.record import Record, prose


if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    "ShapeRecord",
    "catalogue",
    "parse_shape",
    "verify_shape",
]


@dataclass(frozen=True)
class ShapeRecord(Record):
    """One Shape class: the prose, plus one flat entry per slot."""

    entries: tuple[Entry, ...] = ()


def parse_shape(cls: type, path: str = "", *, aliases: tuple[str, ...] = ()) -> ShapeRecord:
    """One ShapeRecord for ``cls``. Slots are listed, not expanded."""
    blocks = split_docstring(cls.__doc__)
    where = path or f"{cls.__module__}.{cls.__name__}"
    return ShapeRecord(
        **prose(cls, cls.__name__, where, blocks, aliases=aliases),
        entries=entries_of(cls, where),
    )


def catalogue(module: ModuleType) -> tuple[ShapeRecord, ...]:
    """A ShapeRecord per Shape the module declares, in export order.

    A Shape is declared, not exported by nu, so this is not the entry point
    the other kinds' catalogues are - ``parse_shape`` is. It exists for the
    one question that comes before any of it: an agent pointed at an app
    module asking what is in here.
    """
    name = module.__name__
    return tuple(
        parse_shape(  # type: ignore[arg-type]
            member.target, path=f"{name}.{member.name}", aliases=member.aliases
        )
        for member in public_members(module)
        if is_shape(member.target)
    )


def verify_shape(cls: type) -> list[Violation]:
    """Every way ``cls`` lies about the format.

    Adds the two removals to the shared laws: a declarative class that is
    never called cannot honestly carry Args or Yields. That slots must not be
    enumerated in prose is the other half of the contract and is deliberately
    not checked - a note about one slot is often the only place a real
    invariant is written, and this runs over the whole stack, where a false
    positive sends someone to rewrite a docstring that was right.
    """
    name = cls.__name__
    blocks = split_docstring(cls.__doc__)
    violations = check_summary(name, blocks)
    violations.extend(check_absent(name, blocks, *ARGS, rule="args-not-callable"))
    violations.extend(check_absent(name, blocks, *YIELDS, rule="yields-not-a-term"))
    violations.extend(check_example(name, blocks))
    return violations
