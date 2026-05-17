"""Program: a compiled program, the description plus the attr relation.

Compilation evaluates every attribute on every node. The only thing stored is
the attr(path, name, value) relation; the description is held by reference.
Evaluation is directional: synthesized folds bottom-up, inherited threads
top-down, in the topological order of the schema's dependency graph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from nu.engine.attribute import Attribute, Schema
    from nu.engine.symbol import Symbol

__all__ = ["Attr", "Path", "Program", "Row", "Rows", "compile"]

type Path = tuple[int, ...]
type Row = dict[str, object]


class Rows(list):
    """A query result: rows of {path, name, value}, with filters."""

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
    """The attr(path, name, value) relation: point read and relation query.

    It is also the evaluation memo: a computed value is written exactly once.
    """

    def __init__(self, program: Program) -> None:
        self._program = program
        self._rows: dict[tuple[Path, str], object] = {}

    def __call__(self, path: Path, name: str) -> object:
        """Point read: the value of attribute ``name`` at ``path``."""
        return self._program._read(path, name)

    def rows(self, name: str | None = None, under: Path | None = None) -> Rows:
        """The relation as rows, optionally filtered by name or by subtree."""
        out = Rows()
        for (path, attr_name), value in self._rows.items():
            if name is not None and attr_name != name:
                continue
            if under is not None and path[: len(under)] != under:
                continue
            out.append({"path": path, "name": attr_name, "value": value})
        return out

    def __repr__(self) -> str:
        return f"Attr({len(self._rows)} rows)"


class Program:
    """A compiled program: the description held by reference, plus ``attr``."""

    root: Path = ()

    def __init__(self, description: Symbol, schema: Schema) -> None:
        self._description = description
        self._schema = schema
        self.attr = Attr(self)

    # --- structure: read straight off the held description, never copied ---

    def symbol(self, path: Path) -> Symbol:
        """The Symbol at ``path``."""
        node = self._description
        for slot in path:
            node = node.children[slot]
        return node

    def kind(self, path: Path) -> type[Symbol]:
        """The kind (class) of the Symbol at ``path``."""
        return type(self.symbol(path))

    def payload(self, path: Path) -> dict[str, object]:
        """The payload of the Symbol at ``path``."""
        return self.symbol(path).payload

    def parent(self, path: Path) -> Path | None:
        """The parent path, or None at the root."""
        return path[:-1] if path else None

    def children(self, path: Path) -> list[Path]:
        """The child paths of ``path``."""
        count = len(self.symbol(path).children)
        return [(*path, slot) for slot in range(count)]

    def walk(self, under: Path = ()) -> Iterator[Path]:
        """Enumerate every path under ``under``, that node first (preorder)."""
        yield under
        for child in self.children(under):
            yield from self.walk(child)

    # --- evaluation: directional, fills attr; the relation is the memo ---

    def _read(self, path: Path, name: str) -> object:
        """Read attribute ``name`` at ``path``.

        Declared attributes are schema constants. Computed attributes are read
        from ``attr``, which ``compile`` has fully populated.
        """
        attribute = self._schema.attribute(self.kind(path), name)
        if attribute is None:
            raise KeyError(f"{self.kind(path).__name__} has no attribute {name!r}")
        if attribute.flavor == "declared":
            return attribute.value
        return self.attr._rows[path, name]

    def _compile(self) -> None:
        """Force every computed attribute on every node, in dependency order."""
        for name in self._schema.order():
            attribute = self._schema._global[name]
            if attribute.flavor == "synthesized":
                self._sweep_synthesized(name, attribute)
            else:
                self._sweep_inherited(name, attribute)

    def _sweep_synthesized(self, name: str, attribute: Attribute) -> None:
        """Fill a synthesized attribute, children before parents."""
        for path in self._postorder():
            own = attribute.base(self, path)
            child_values = [self.attr._rows[child, name] for child in self.children(path)]
            self.attr._rows[path, name] = attribute.combine(own, child_values)

    def _sweep_inherited(self, name: str, attribute: Attribute) -> None:
        """Fill an inherited attribute, parents before children."""
        for path in self.walk():
            if not path:
                value = attribute.root(self, path)
            else:
                parent_value = self.attr._rows[path[:-1], name]
                value = attribute.derive(self, path[:-1], path[-1], parent_value)
            self.attr._rows[path, name] = value

    def _postorder(self, under: Path = ()) -> Iterator[Path]:
        """Enumerate every path under ``under``, children before that node."""
        for child in self.children(under):
            yield from self._postorder(child)
        yield under

    def __repr__(self) -> str:
        return f"Program({self._description!r}, {self.attr!r})"


def compile(description: Symbol, schema: Schema) -> Program:
    """Construct then compile: evaluate every attribute on every node.

    Args:
        description: the root Symbol of the application.
        schema: a finalized Schema.

    Returns:
        A compiled Program with ``attr`` fully populated.
    """
    program = Program(description, schema)
    program._compile()
    return program
