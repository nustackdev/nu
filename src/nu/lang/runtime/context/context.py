"""Context - the environment a task runs against.

A Context is a stack of immutable frames holding fabrics: execution resources,
storage handles, the mem dicts Shapes read. ``bind`` / ``lazy`` push a frame
and return a new Context; nothing is ever changed in place or restored, so a
Context can be shared by any number of tasks and anything holding one keeps
its frames alive.

Lookup walks the frames top down. Per key (fabric type plus scope tags, plus
the predicate set for a guarded binding) the nearest frame wins, and across
keys the specificity rules choose: exact tags, then subset fallback, then the
untagged binding; predicate guards are evaluated against the ``**data`` given
to ``get``.

Usage:
    ctx = Context()
    ctx = ctx.bind(Storage, rocksdb)
    ctx = ctx.bind(View, shard_a, Market, sharding=lambda site, path: site[0] < 16)

    ctx.get(Storage)                                # -> rocksdb
    ctx.get(View, Market, site=(5,), path=(...,))   # -> shard_a

``ctx.attrs`` is the flat name store interactions still bind their values in.
It is temporary: it goes away once every binding hands its values through
mem (task-184 phase 4).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

from .attributes import Attributes
from .fabrics import _Entry, _find, _Frame, _missing, _view


_T = TypeVar("_T")


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


__all__ = ["Context"]


class Context:
    """One task's environment: a stack of fabric frames (and, for now, an attrs store).

    Args:
        attrs: names the Context starts with, e.g. a worker handoff or a
            dispatch seed. Temporary, see the module docstring.
    """

    __slots__ = ("_attrs", "_top")

    def __init__(self, attrs: Mapping[str, object] | None = None) -> None:
        self._attrs = Attributes(dict(attrs) if attrs else None)
        self._top: _Frame | None = None

    # -- attrs (temporary) ---------------------------------------------------

    @property
    def attrs(self) -> Attributes:
        """The name store attrs refs read and write. Temporary, see the module docstring."""
        return self._attrs

    def _fork_attrs(self) -> Context:
        """The same frames with an own copy of the attrs table.

        TEMPORARY (task-184 phase 4 deletes attrs and this with it): a
        concurrent arm takes this so a name it binds in attrs stays in the
        arm. Frames need no copy, they are immutable.
        """
        ctx = Context.__new__(Context)
        ctx._attrs = self._attrs._branch()
        ctx._top = self._top
        return ctx

    # -- push ----------------------------------------------------------------

    def bind(
        self,
        fabric_type: type[_T],
        value: _T,
        *tags: object,
        **predicates: Callable,
    ) -> Context:
        """A new Context with a frame providing ``value`` under ``fabric_type`` and ``tags``.

        The frame shadows a binding of the same key below it.

        Args:
            fabric_type: Primary key (type).
            value: The value to bind.
            *tags: Scope tags for specificity.
            **predicates: Named guard callables. Each receives **data from get().
        """
        return self._push(fabric_type, tags, predicates, _Entry.eager(value))

    def lazy(
        self,
        fabric_type: type[_T],
        factory: Callable[[], _T],
        *tags: object,
        **predicates: Callable,
    ) -> Context:
        """A new Context with a frame providing ``factory``'s value, built on first lookup.

        The factory is called once, under a lock, however many tasks look it
        up first at the same time; the value is cached in this frame.

        Args:
            fabric_type: Primary key (type).
            factory: Zero-arg callable that creates the value.
            *tags: Scope tags for specificity.
            **predicates: Named guard callables.
        """
        return self._push(fabric_type, tags, predicates, _Entry.deferred(factory))

    def _push(
        self,
        fabric_type: object,
        tags: tuple[object, ...],
        predicates: dict[str, Callable],
        entry: _Entry,
    ) -> Context:
        ctx = Context.__new__(Context)
        ctx._attrs = self._attrs
        ctx._top = _Frame(self._top, fabric_type, frozenset(tags), dict(predicates), entry)
        return ctx

    # -- reads ---------------------------------------------------------------

    def get(self, fabric_type: type[_T], *tags: object, **data: object) -> _T:
        """Resolve the most specific binding by fabric type + scope tags.

        Args:
            fabric_type: Primary key (type).
            *tags: Scope tags to match against.
            **data: Passed as **kwargs to all predicates.

        Raises:
            LookupError: nothing in scope matches.
        """
        scope_tags = frozenset(tags)
        entry = _find(self._top, fabric_type, scope_tags, data)
        if entry is None:
            raise _missing(fabric_type, scope_tags, data)
        return cast("_T", entry.resolve())

    def has(self, fabric_type: type, *tags: object) -> bool:
        """Whether a binding for fabric type + optional scope tags is in scope.

        A lazy binding found here is built, the same as ``get`` builds it.
        """
        entry = _find(self._top, fabric_type, frozenset(tags), {})
        if entry is None:
            return False
        entry.resolve()
        return True

    def was_opened(self, fabric_type: type, *tags: object) -> bool:
        """Whether the plain binding at exactly these tags is lazy and was built."""
        entry = _view(self._top, fabric_type)[0].get(frozenset(tags))
        return entry is not None and entry.was_opened

    def predicates(self, fabric_type: type, *tags: object) -> list[tuple[dict, object]]:
        """``(predicates, value)`` for each guarded binding at exactly these tags, outermost first."""
        scope_tags = frozenset(tags)
        return [
            (dict(g.predicates), g.entry.resolve())
            for g in _view(self._top, fabric_type)[1]
            if g.scope_tags == scope_tags
        ]

    # -- repr ----------------------------------------------------------------

    def __repr__(self) -> str:
        labels: list[str] = []
        frame = self._top
        while frame is not None:
            labels.append(frame.label())
            frame = frame.parent
        return f"Context({self._attrs!r}, [{', '.join(reversed(labels))}])"
