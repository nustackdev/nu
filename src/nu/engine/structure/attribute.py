"""Attribute: a named value on a Term class.

An attribute is one of three concrete kinds:

- :class:`Declared` -- a constant baked into the class. Just data.
- :class:`Synthesized` -- a bottom-up fold: own value via ``base``, combined
  with the values at the children via ``combine``.
- :class:`Inherited` -- a top-down thread: a value via ``root`` at the root,
  derived from the parent's value below it.

The two computed kinds share :class:`Computed` as their base, which carries
``reads`` -- the names of the attributes their rules consult. Those reads are
the edges of the cross-attribute dependency graph; the graph and its
topological order live on the :class:`~nu.engine.structure.schema.Schema`.

Construction shapes are keyword-only and per-kind. ``Attribute`` and
``Computed`` are abstract bases; do not instantiate them directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .types import RuleFn

__all__ = ["Attribute", "Computed", "Declared", "Inherited", "Synthesized"]


@dataclass(kw_only=True)
class Attribute:
    """Abstract base: a named value on a Term class.

    Concrete kinds are :class:`Declared`, :class:`Synthesized`,
    :class:`Inherited`. ``name`` is optional at construction: for tree-wide
    attributes pass it explicitly; for class-body attributes the
    :class:`~nu.engine.structure.term.TermMeta` metaclass fills it in from
    the binding name.
    """

    name: str | None = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r})"


@dataclass(kw_only=True, repr=False)
class Declared(Attribute):
    """A constant attribute: schema data baked onto the class.

    Read straight off the class via the schema; never stored on a Program.
    A tree-wide ``Declared`` can register a default that any kind overrides
    in its own class body.
    """

    value: object


@dataclass(kw_only=True, repr=False)
class Computed(Attribute):
    """Abstract base for a computed attribute.

    Computed attributes are produced during the compile phase and stored as
    columns on the Program. ``reads`` declares the other attributes the rules
    consult; the schema topologically sorts the read-graph at finalize.
    """

    reads: tuple[str, ...] = ()


@dataclass(kw_only=True, repr=False)
class Synthesized(Computed):
    """A bottom-up attribute.

    Two rules:

    - ``base(program, path) -> own_value`` at every node, producing the
      node's contribution.
    - ``combine(own, child_values) -> value`` folds the own value with the
      ordered list of child values. At a leaf, ``child_values`` is empty,
      so the fold bottoms out on ``base`` alone.

    ``combine`` is the one pure rule: it gets no ``program`` handle, only
    ``own`` and the child values. This keeps it a pure merge operator and
    forbids it from breaking directionality.
    """

    base: RuleFn
    combine: RuleFn


@dataclass(kw_only=True, repr=False)
class Inherited(Computed):
    """A top-down attribute.

    Two rules:

    - ``root(program, path) -> value`` at the root.
    - ``derive(program, parent_path, slot, parent_value) -> value`` at every
      non-root node, where ``parent_path`` is the parent's path and ``slot``
      the child index under it.

    ``derive`` may read a sibling's *synthesized* attribute in the same step;
    this is the bridge that lets one rule combine top-down and bottom-up
    information without a fourth flavor.
    """

    root: RuleFn
    derive: RuleFn
