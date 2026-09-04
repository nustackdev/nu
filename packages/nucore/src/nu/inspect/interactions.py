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
from typing import TYPE_CHECKING

from nu.inspect.form import parse_form
from nu.inspect.interaction import parse_interaction
from nu.inspect.ref import parse_ref
from nu.lang import ScalarQuery
from nu.lang.kinds import Interaction, Ref
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from nu.inspect.call import CallRecord
    from nu.inspect.interaction import InteractionRecord
    from nu.inspect.record import Record
    from nu.lang.runtime import Runtime


__all__ = ["Inspect", "render"]


class Inspect(ScalarQuery):
    """Docs for a Nu module or subject, as formatted text.

    Args:
        path: a dotted path. Either a module (``nu.core.arithmetic``,
            ``nu.forms.primitives``) or a fully qualified atom
            (``nu.core.arithmetic.Add``, ``nu.forms.primitives.Int``).
            Resolution tries module import first, then falls back to
            ``parent.attr``.

    Notes:
        - Yields a string laid out for reading, not a structured record. The
          shape is stable but not part of the contract - treat it as docs.
        - A module renders every Form, Ref and Interaction it exports, in
          that order, with a short header per subject.
        - An atom renders the full record for that one subject.

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
    if isinstance(target, type):
        return _render_class(target, path)
    return _render_module(target)


# --- resolution ----------------------------------------------------------


def _resolve(path: str) -> object | None:
    """A module for a module path, a class for an atom path, else None."""
    try:
        return importlib.import_module(path)
    except ModuleNotFoundError:
        pass
    if "." not in path:
        return None
    parent_path, _, attr = path.rpartition(".")
    try:
        parent = importlib.import_module(parent_path)
    except ModuleNotFoundError:
        return None
    return getattr(parent, attr, None)


# --- module ---------------------------------------------------------------


def _render_module(module: ModuleType) -> str:
    from nu.inspect.form import catalogue as forms_of
    from nu.inspect.interaction import catalogue as interactions_of
    from nu.inspect.ref import catalogue as refs_of

    parts: list[str] = [f"MODULE  {module.__name__}", ""]
    doc = (module.__doc__ or "").strip()
    if doc:
        parts.extend([doc, ""])

    forms = forms_of(module)
    refs = refs_of(module)
    interactions = interactions_of(module)

    if not (forms or refs or interactions):
        parts.append("(no Nu subjects exported)")
        return "\n".join(parts)

    if forms:
        parts.append(f"FORMS ({len(forms)})")
        for r in forms:
            parts.append(f"  {r.name:<20}  {r.summary or '-'}")
        parts.append("")
    if refs:
        parts.append(f"REFS ({len(refs)})")
        for r in refs:
            parts.append(f"  {r.name:<20}  {r.summary or '-'}")
        parts.append("")
    if interactions:
        parts.append(f"INTERACTIONS ({len(interactions)})")
        for r in interactions:
            parts.append(f"  {r.name:<20}  {r.summary or '-'}")
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


# --- class ----------------------------------------------------------------


def _render_class(cls: type, path: str) -> str:
    from nu.lang import Form

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


def _render_builder(record: Record, *, kind: str) -> str:
    parts: list[str] = [
        f"{kind}  {record.path}",
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
