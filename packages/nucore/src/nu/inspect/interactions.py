"""Inspection atoms: the info records rendered as docs an agent can read.

One atom, ``Inspect``, that resolves a dotted path to a module or a Nu
subject (Form, Ref, Interaction) and yields the same six-section format the
author wrote by hand - summary, description, args, notes, yields, examples -
laid out for reading, not for programmatic descent. When an agent needs to
know what an atom takes or what a module exposes, it composes ``Inspect``
into its program, evaluates, and reads the yielded string.

Keeping this atom-shaped (rather than a Python helper) is deliberate: the
lookup is composable with the rest of an agent's Nu, and the result flows
back through the same observation path as any other yield.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.inspect.entry import entry_names, is_service, is_shape, nested_shape, parse_entry
from nu.inspect.form import parse_form
from nu.inspect.interaction import parse_interaction
from nu.inspect.ref import parse_ref
from nu.inspect.service import parse_service
from nu.inspect.shape import ShapeRecord, parse_shape
from nu.lang import ScalarQuery
from nu.lang.kinds import Interaction, Ref
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from nu.inspect.call import CallRecord
    from nu.inspect.entry import Entry
    from nu.inspect.interaction import InteractionRecord
    from nu.inspect.record import Record
    from nu.lang.runtime import Runtime


__all__ = ["Inspect", "render"]


class Inspect(ScalarQuery):
    """Docs for a Nu module or subject, as formatted text.

    Args:
        path: a dotted path. A module (``nu.core.arithmetic``,
            ``myapp.shapes``), a fully qualified subject
            (``nu.core.arithmetic.Add``, ``myapp.shapes.Task``), or one entry
            of a declared class (``myapp.shapes.Task.title``). Resolution
            imports the longest module prefix, then walks what is left.

    Notes:
        - Yields a string laid out for reading, not a structured record. The
          shape is stable but not part of the contract - treat it as docs.
        - A module renders every Shape, Service, Form, Ref and Interaction it
          holds, with a short header per subject.
        - An atom renders the full record for that one subject.
        - A Shape or Service renders its prose and one line per entry, never
          the entries themselves: the reader descends by looking up the entry
          path it wants. Walking through a nested Shape slot works the same
          way, so ``myapp.Task.owner.email`` resolves.

    Yields:
        The formatted text. INVALID when the path resolves to nothing that
        nu.inspect can describe.

    Example:
        >>> nu.run(nu.inspect.Inspect("nu.core.arithmetic"))[0].splitlines()[0]
        'MODULE  nu.core.arithmetic'
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (child,) = children

        def thunk(rt: Runtime) -> object:
            v = child(rt)
            if v is EMPTY or v is INVALID or not isinstance(v, str):
                return INVALID
            text = render(v)
            return text if text else INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (child,) = children

        async def athunk(rt: Runtime) -> object:
            v = await child(rt)
            if v is EMPTY or v is INVALID or not isinstance(v, str):
                return INVALID
            text = render(v)
            return text if text else INVALID

        return athunk


def render(path: str) -> str:
    """Resolve ``path`` and render whatever it points at, or empty on miss."""
    target = _resolve(path)
    if target is None:
        return ""
    if isinstance(target, _EntryPath):
        return _render_entry(target, path)
    if isinstance(target, type):
        return _render_class(target, path)
    return _render_module(target)


# --- resolution ----------------------------------------------------------


@dataclass(frozen=True)
class _EntryPath:
    """One entry of a declared class, reached by a path. Not a class itself."""

    owner: type
    name: str


def _resolve(path: str) -> object | None:
    """A module, a class, one entry of a declared class, or None.

    Imports the longest prefix of ``path`` that is a module and walks the
    rest. The plain ``parent.attr`` fallback is not enough once Shapes are in
    scope: a slot lives two or more names below its module, and reading it
    off the class with ``getattr`` runs the descriptor and hands back a Ref
    instance, losing the declaration the reader asked about.
    """
    try:
        return importlib.import_module(path)
    except ModuleNotFoundError:
        pass
    parts = path.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        try:
            module = importlib.import_module(".".join(parts[:cut]))
        except ModuleNotFoundError:
            continue
        return _walk(module, parts[cut:])
    return None


def _walk(target: object, names: list[str]) -> object | None:
    """Follow ``names`` from ``target``, stepping through declared entries."""
    for index, name in enumerate(names):
        if name in entry_names(target):
            if index == len(names) - 1:
                return _EntryPath(target, name)
            nested = nested_shape(target, name)  # type: ignore[arg-type]
            if nested is None:
                return None
            target = nested
            continue
        target = getattr(target, name, None)
        if target is None:
            return None
    return target


# --- module ---------------------------------------------------------------


def _render_module(module: ModuleType) -> str:
    from nu.inspect.form import catalogue as forms_of
    from nu.inspect.interaction import catalogue as interactions_of
    from nu.inspect.ref import catalogue as refs_of
    from nu.inspect.service import catalogue as services_of
    from nu.inspect.shape import catalogue as shapes_of

    parts: list[str] = [f"MODULE  {module.__name__}", ""]
    doc = (module.__doc__ or "").strip()
    if doc:
        parts.extend([doc, ""])

    # Shapes and Services first: in an app module they are the subject, and
    # everything else in the file is written against them.
    sections = (
        ("SHAPES", shapes_of(module)),
        ("SERVICES", services_of(module)),
        ("FORMS", forms_of(module)),
        ("REFS", refs_of(module)),
        ("INTERACTIONS", interactions_of(module)),
    )
    if not any(records for _, records in sections):
        parts.append("(no Nu subjects exported)")
        return "\n".join(parts)

    for label, records in sections:
        if not records:
            continue
        parts.append(f"{label} ({len(records)})")
        for r in records:
            parts.append(f"  {r.name:<20}  {r.summary or '-'}")
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


# --- class ----------------------------------------------------------------


def _render_class(cls: type, path: str) -> str:
    from nu.lang import Form

    # Shape and Service first: neither is a Nu term at all, so they cannot be
    # confused with the three below, and the check is a marker lookup.
    if is_shape(cls):
        return _render_declaration(parse_shape(cls, path=path), kind="SHAPE")
    if is_service(cls):
        return _render_declaration(parse_service(cls, path=path), kind="SERVICE")
    # Order matters: Refs inherit Nu, Forms inherit Interaction, so the most
    # specific dispatch wins - Ref before Form before Interaction.
    if issubclass(cls, Ref):
        record = parse_ref(cls, path=path)
        return _render_builder(record, kind="REF")
    if issubclass(cls, Form):
        record = parse_form(cls, path=path)
        return _render_builder(record, kind="FORM")
    if issubclass(cls, Interaction):
        record = parse_interaction(cls, path=path)
        return _render_interaction(record)
    return ""


def _render_interaction(record: InteractionRecord) -> str:
    parts: list[str] = [
        f"INTERACTION  {record.path}",
        "",
        f"  {record.summary or '-'}",
    ]
    if record.description:
        parts.extend(["", record.description])
    parts.extend(_common_body(record))
    if record.yields:
        parts.extend(["", "  yields", f"    {record.yields}"])
    parts.extend(_examples_lines(record.examples))
    return "\n".join(parts).rstrip() + "\n"


def _render_declaration(record: Record, *, kind: str) -> str:
    """A Shape or a Service: prose, then one line per entry. Two levels, no tree."""
    parts: list[str] = [f"{kind}  {record.path}", "", f"  {record.summary or '-'}"]
    if record.description:
        parts.extend(["", record.description])
    parts.extend(_common_body(record))
    parts.extend(_examples_lines(record.examples))

    entries: tuple[Entry, ...] = getattr(record, "entries", ())
    if not entries:
        parts.extend(["", "  (declares nothing)"])
        return "\n".join(parts).rstrip() + "\n"
    parts.extend(["", f"  entries ({len(entries)})"])
    for e in entries:
        config = f"  {e.config}" if e.config else ""
        parts.append(f"    {e.name:<20} {e.kind:<7} {e.type}{config}")
    parts.extend(["", f"  inspect one with {record.path}.<name>"])
    return "\n".join(parts).rstrip() + "\n"


def _render_entry(entry: _EntryPath, path: str) -> str:
    """One entry, rendered as whatever record already covers it."""
    record = parse_entry(entry.owner, entry.name, path=path)
    if record is None:
        return ""
    if isinstance(record, ShapeRecord):
        return _render_declaration(record, kind="SHAPE")
    return _render_builder(record, kind="REF")


def _render_builder(record: Record, *, kind: str) -> str:
    # An entry's path is where it was reached, not where its class lives, so
    # name the class when the path does not already end in it.
    named = "" if record.path.endswith(f".{record.name}") else f"  ({record.name})"
    parts: list[str] = [
        f"{kind}  {record.path}{named}",
        "",
        f"  {record.summary or '-'}",
    ]
    if record.description:
        parts.extend(["", record.description])
    parts.extend(_common_body(record))
    parts.extend(_examples_lines(record.examples))

    methods: tuple[CallRecord, ...] = getattr(record, "methods", ())
    if methods:
        parts.extend(["", f"  methods ({len(methods)})"])
        for m in methods:
            returns = f" -> {m.returns}" if m.returns else ""
            parts.append(f"    {m.spelling:<24} {returns:<28} {m.summary or ''}")
    return "\n".join(parts).rstrip() + "\n"


# --- shared body pieces ---------------------------------------------------


def _common_body(record: Record) -> list[str]:
    lines: list[str] = []
    args = getattr(record, "args", ())
    if args:
        lines.extend(["", "  args"])
        for arg in args:
            default = f" = {arg.default}" if arg.default else ""
            lines.append(f"    {arg.name}{default}: {arg.text or '-'}")
    if record.notes:
        lines.extend(["", "  notes"])
        for note in record.notes:
            lines.append(f"    - {note}")
    return lines


def _examples_lines(examples: tuple) -> list[str]:
    if not examples:
        return []
    lines = ["", f"  examples ({len(examples)})"]
    for i, ex in enumerate(examples, start=1):
        tag = f"[{i}] " if len(examples) > 1 else ""
        lines.append(f"    {tag}{ex.code or '-'}")
        if ex.expected:
            lines.append(f"    {' ' * len(tag)}-> {ex.expected}")
    return lines
