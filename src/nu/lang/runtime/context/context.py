"""Context - the environment a task runs against.

Two stores, each owning its own scoping:

- ``ctx.attrs`` - flat name store. Refs read and write here; a name comes
  into scope with ``attrs.let``.
- ``ctx.fabrics`` - typed fabric bindings with scope tags and predicate
  guards. Execution resources live here; a binding comes into scope with
  ``fabrics.bind`` / ``fabrics.lazy``.

A Context belongs to one task. Scopes inside the task open ``with`` blocks on
its stores and never replace the Context; a task that starts takes its own
with ``branch()``.

Setup builds the starting Context: ``Context(attrs=...)`` seeds names, and
``bind`` / ``lazy`` return a new Context with one more fabric provided.

Usage:
    ctx = Context(attrs={"n": 1})
    ctx = ctx.bind(Storage, rocksdb)
    ctx = ctx.bind(View, shard_a, Market, sharding=lambda site, path: site[0] < 16)

    ctx.fabrics.get(Storage)                        # -> rocksdb
    ctx.fabrics.get(View, Market, site=(5,), path=(...,))   # -> shard_a
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from .attributes import Attributes
from .fabrics import Fabrics, _Entry


_T = TypeVar("_T")


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


__all__ = ["Context"]


class Context:
    """One task's environment: an attrs store and a fabrics store.

    Args:
        attrs: names the Context starts with, e.g. a worker handoff or a
            dispatch seed.
    """

    __slots__ = ("_attrs", "_fabrics")

    def __init__(self, attrs: Mapping[str, object] | None = None) -> None:
        self._attrs = Attributes(dict(attrs) if attrs else None)
        self._fabrics = Fabrics()

    # -- stores --------------------------------------------------------------

    @property
    def attrs(self) -> Attributes:
        """The name store Refs read and write."""
        return self._attrs

    @property
    def fabrics(self) -> Fabrics:
        """The typed binding store execution resources resolve from."""
        return self._fabrics

    # -- setup ---------------------------------------------------------------

    def bind(
        self,
        fabric_type: type[_T],
        value: _T,
        *tags: object,
        **predicates: Callable,
    ) -> Context:
        """A new Context with ``value`` provided under ``fabric_type`` and ``tags``.

        Args:
            fabric_type: Primary key (type).
            value: The value to bind.
            *tags: Scope tags for specificity.
            **predicates: Named guard callables. Each receives **data from get().
        """
        return self._with(fabric_type, tags, predicates, _Entry.eager(value))

    def lazy(
        self,
        fabric_type: type[_T],
        factory: Callable[[], _T],
        *tags: object,
        **predicates: Callable,
    ) -> Context:
        """A new Context with ``factory`` provided lazily: called on first access, cached.

        Args:
            fabric_type: Primary key (type).
            factory: Zero-arg callable that creates the value.
            *tags: Scope tags for specificity.
            **predicates: Named guard callables.
        """
        return self._with(fabric_type, tags, predicates, _Entry.deferred(factory))

    def _with(
        self,
        fabric_type: type,
        tags: tuple[object, ...],
        predicates: dict[str, Callable],
        entry: _Entry,
    ) -> Context:
        """Branch, then provide ``entry`` on the branch for its whole life."""
        ctx = self.branch()
        ctx._fabrics._put(fabric_type, frozenset(tags), predicates, entry)
        return ctx

    # -- branch --------------------------------------------------------------

    def branch(self) -> Context:
        """The Context a starting task takes: own tables, shared values.

        Both stores get their own tables, so a scope opened or a name set on
        the branch stays on the branch. Values and fabric instances are the
        same objects, so a live handle crosses intact and an object mutated
        in place is seen by everyone.
        """
        ctx = Context.__new__(Context)
        ctx._attrs = self._attrs._branch()
        ctx._fabrics = self._fabrics._branch()
        return ctx

    # -- repr ----------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Context({self._attrs!r}, {self._fabrics!r})"
