"""Attr: the attr relation view, plus the Row / Rows query result types.

Storage lives on the AttributedTerm as ``attrs: dict[name, list[value]]``
indexed by ``nid``. ``Attr`` is a thin shim over it:

- ``__call__(path, name)``  - point read by path (resolves nid, then list index)
- ``rows(name=, under=)``   - walk the columns and project ``Rows``

A ``Row`` is one tuple ``{"path", "name", "value"}``. ``Rows`` is the result
type: a list of rows with chainable filters (``where``) and projections
(``paths``, ``values``).

The hot path bypasses ``Attr`` entirely and reads ``program.attrs[name][nid]``
directly. ``Attr`` is the cold-path / public API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.engine.attribution.attributed_term import AttributedTerm, Path

__all__ = ["Attr", "Row", "Rows"]

type Row = dict[str, object]


class Rows(list):
    """A query result: rows of ``{path, name, value}`` with filters and projections."""

    def where(self, predicate: Callable[[Row], bool]) -> Rows:
        """The rows for which ``predicate`` holds."""
        return Rows(row for row in self if predicate(row))

    def paths(self) -> list[Path]:
        """The path of each row."""
        return [row["path"] for row in self]

    def values(self) -> list[object]:
        """The value of each row."""
        return [row["value"] for row in self]


class Attr:
    """The attr relation, callable for point reads and queryable for rows."""

    def __init__(self, program: AttributedTerm) -> None:
        self._program = program

    def __call__(self, path: Path, name: str) -> object:
        """Point read: the value of attribute ``name`` at ``path``."""
        return self._program._read(path, name)

    def rows(self, name: str | None = None, under: Path | None = None) -> Rows:
        """The relation as rows, optionally filtered by name or by subtree."""
        program = self._program
        path_of = program.path_of
        names = (name,) if name is not None else tuple(program.attrs)
        prefix_len = len(under) if under is not None else 0

        out = Rows()
        for attr_name in names:
            column = program.attrs.get(attr_name)
            if column is None:
                continue
            for nid, value in enumerate(column):
                p = path_of[nid]
                if under is not None and p[:prefix_len] != under:
                    continue
                out.append({"path": p, "name": attr_name, "value": value})
        return out

    def __repr__(self) -> str:
        total = sum(len(col) for col in self._program.attrs.values())
        return f"Attr({total} rows)"
