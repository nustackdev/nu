"""Fabrics - the typed binding store behind ``ctx.fabrics``.

Execution resources (storage, RPC clients, sessions, ...) live here, keyed by
fabric type plus optional scope tags and predicate guards. A binding comes
into scope with ``bind`` / ``lazy`` and leaves when that scope ends, whatever
ends it, the same discipline ``Attributes.let`` gives names.

Resolution matches by fabric type first, then scope tags with subset
fallback; predicate kwargs are evaluated against the ``**data`` passed to
``get``.

Usage:
    fabrics = ctx.fabrics
    with fabrics.bind(Storage, rocksdb), fabrics.bind(Storage, order_db, OrderShape):
        fabrics.get(Storage)                        # -> rocksdb
        fabrics.get(Storage, OrderShape)            # -> order_db
    fabrics.has(Storage)                            # -> False
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast


if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from types import TracebackType


_T = TypeVar("_T")


__all__ = ["Fabrics"]


def _name(tag: object) -> str:
    """Human-readable name for a tag."""
    return getattr(tag, "__name__", None) or repr(tag)


# ---------------------------------------------------------------------------
# Entries: the atoms of the store
# ---------------------------------------------------------------------------


class _Entry:
    """One binding - eager (value) or lazy (factory, cached on first access)."""

    __slots__ = ("_factory", "_resolved", "_value", "_was_lazy")

    @staticmethod
    def eager(value: object) -> _Entry:
        """Create an eager (pre-resolved) entry."""
        e = _Entry.__new__(_Entry)
        e._value = value
        e._factory = None
        e._resolved = True
        e._was_lazy = False
        return e

    @staticmethod
    def deferred(factory: Callable[[], object]) -> _Entry:
        """Create a lazy (deferred) entry."""
        e = _Entry.__new__(_Entry)
        e._value = None
        e._factory = factory
        e._resolved = False
        e._was_lazy = True
        return e

    def resolve(self) -> object:
        """Return the value, calling the factory on first access if lazy."""
        if not self._resolved:
            if self._factory is not None:
                self._value = self._factory()
                self._factory = None
            self._resolved = True
        return self._value

    @property
    def was_opened(self) -> bool:
        """True if this was a lazy entry that has been resolved."""
        return self._was_lazy and self._resolved

    @property
    def is_lazy(self) -> bool:
        """True if this entry was registered as lazy (regardless of resolution)."""
        return self._was_lazy


class _GuardedEntry:
    """A predicate-guarded binding. All predicates must pass for a match."""

    __slots__ = ("entry", "predicates", "scope_tags")

    def __init__(
        self,
        scope_tags: frozenset,
        predicates: dict[str, Callable],
        entry: _Entry,
    ) -> None:
        self.scope_tags = scope_tags
        self.predicates = predicates
        self.entry = entry

    def matches(self, data: dict) -> bool:
        """True if all predicates pass with the given data kwargs."""
        return all(pred(**data) for pred in self.predicates.values())


# ---------------------------------------------------------------------------
# Fabrics
# ---------------------------------------------------------------------------


class Fabrics:
    """Typed binding store, and the one owner of fabric scoping.

    ``bind`` and ``lazy`` are scopes: entering provides the binding for the
    body and shadows an outer one of the same key, leaving restores what was
    there. Reads resolve the most specific binding in scope.
    """

    __slots__ = ("_entries", "_guarded")

    def __init__(self) -> None:
        self._entries: dict[tuple, _Entry] = {}
        self._guarded: dict[type, list[_GuardedEntry]] = {}

    # -- scopes --------------------------------------------------------------

    def bind(
        self,
        fabric_type: type[_T],
        value: _T,
        *tags: object,
        **predicates: Callable,
    ) -> _Provide:
        """A scope that provides ``value`` under ``fabric_type`` and ``tags``.

        Entering shadows any outer binding of the same key; leaving restores
        it, on a clean exit and on an error alike. A generator may hold the
        scope open across its yields, so a binding over a stream lives while
        the stream is drained.

        Args:
            fabric_type: Primary key (type).
            value: The value to bind.
            *tags: Scope tags for specificity.
            **predicates: Named guard callables. Each receives **data from get().
        """
        return _Provide(self, fabric_type, frozenset(tags), predicates, _Entry.eager(value))

    def lazy(
        self,
        fabric_type: type[_T],
        factory: Callable[[], _T],
        *tags: object,
        **predicates: Callable,
    ) -> _Provide:
        """A scope like ``bind`` whose value is built on first access and cached.

        Args:
            fabric_type: Primary key (type).
            factory: Zero-arg callable that creates the value.
            *tags: Scope tags for specificity.
            **predicates: Named guard callables.
        """
        return _Provide(self, fabric_type, frozenset(tags), predicates, _Entry.deferred(factory))

    def _put(
        self,
        fabric_type: type,
        scope_tags: frozenset,
        predicates: dict[str, Callable],
        entry: _Entry,
    ) -> Callable[[], None]:
        """Install ``entry`` and return the call that puts the prior state back."""
        if predicates:
            guarded = _GuardedEntry(scope_tags, dict(predicates), entry)
            self._guarded.setdefault(fabric_type, []).append(guarded)

            def unguard() -> None:
                entries = self._guarded.get(fabric_type, [])
                if guarded in entries:
                    entries.remove(guarded)
                if not entries:
                    self._guarded.pop(fabric_type, None)

            return unguard

        key = (fabric_type, scope_tags)
        had_prev = key in self._entries
        prev = self._entries.get(key)
        self._entries[key] = entry

        def restore() -> None:
            if had_prev:
                self._entries[key] = prev  # type: ignore[assignment]
            else:
                self._entries.pop(key, None)

        return restore

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
        return cast("_T", self._resolve(fabric_type, frozenset(tags), data))

    def has(self, fabric_type: type, *tags: object) -> bool:
        """Whether a binding for fabric type + optional scope tags is in scope."""
        try:
            self._resolve(fabric_type, frozenset(tags), {})
        except LookupError:
            return False
        return True

    def was_opened(self, fabric_type: type, *tags: object) -> bool:
        """Whether a lazy binding was materialized."""
        entry = self._entries.get((fabric_type, frozenset(tags)))
        return entry is not None and entry.was_opened

    def predicates(self, fabric_type: type, *tags: object) -> list[tuple[dict, object]]:
        """``(predicates, value)`` for each guarded binding at exactly these tags."""
        scope_tags = frozenset(tags)
        return [
            (dict(g.predicates), g.entry.resolve())
            for g in self._guarded.get(fabric_type, [])
            if g.scope_tags == scope_tags
        ]

    # -- resolution ----------------------------------------------------------

    def _resolve(self, fabric_type: type, scope_tags: frozenset, data: dict) -> object:
        """Core resolution with specificity fallback.

        1. Try exact scope tags match.
        2. Subset fallback: try progressively smaller scope tag sets.
        3. Empty scope fallback.
        """
        entry = self._find(fabric_type, scope_tags, data)
        if entry is not None:
            return entry.resolve()

        if len(scope_tags) > 1:
            tags_list = sorted(scope_tags, key=id)
            for size in range(len(scope_tags) - 1, 0, -1):
                for subset in _subsets_of_size(tags_list, size):
                    entry = self._find(fabric_type, frozenset(subset), data)
                    if entry is not None:
                        return entry.resolve()

        if scope_tags:
            entry = self._find(fabric_type, frozenset(), data)
            if entry is not None:
                return entry.resolve()

        tag_names = ", ".join(_name(t) for t in scope_tags)
        data_str = ", ".join(f"{k}={v!r}" for k, v in data.items())
        parts = [_name(fabric_type)]
        if tag_names:
            parts.append(f"[{tag_names}]")
        if data_str:
            parts.append(f"({data_str})")
        msg = f"No binding for: {''.join(parts)}"
        raise LookupError(msg)

    def _find(self, fabric_type: type, scope_tags: frozenset, data: dict) -> _Entry | None:
        """Find entry at exact scope level. Returns None if nothing found.

        If guarded entries exist for this fabric_type with matching scope,
        predicates are evaluated. All predicates on an entry must pass (AND).
        At least one entry must fully match (OR across entries).
        No fallback to non-predicate bindings at same scope if guarded exist.
        """
        guarded = self._guarded.get(fabric_type) if data else None
        if guarded:
            candidates = [g for g in guarded if g.scope_tags == scope_tags]
            if candidates:
                for g in candidates:
                    if g.matches(data):
                        return g.entry
                return None

        return self._entries.get((fabric_type, scope_tags))

    # -- branch --------------------------------------------------------------

    def _branch(self) -> Fabrics:
        """Own tables, same entries: a scope opened on the copy stays on the copy."""
        fabrics = Fabrics.__new__(Fabrics)
        fabrics._entries = dict(self._entries)
        fabrics._guarded = {k: list(v) for k, v in self._guarded.items()}
        return fabrics

    # -- repr ----------------------------------------------------------------

    def __repr__(self) -> str:
        parts: list[str] = []
        for (stype, stags), entry in self._entries.items():
            labels = [_name(stype), *(_name(t) for t in stags)]
            if entry.is_lazy:
                labels.append("lazy")
            parts.append("+".join(labels))
        for stype, entries in self._guarded.items():
            for g in entries:
                labels = [_name(stype), *(_name(t) for t in g.scope_tags)]
                labels.append("+".join(g.predicates))
                parts.append("+".join(labels))
        return f"Fabrics({', '.join(parts)})"


class _Provide:
    """One ``bind`` / ``lazy`` scope: provides on enter, puts the prior state back on exit."""

    __slots__ = ("_entry", "_fabric_type", "_predicates", "_restore", "_scope_tags", "_store")

    def __init__(
        self,
        store: Fabrics,
        fabric_type: type,
        scope_tags: frozenset,
        predicates: dict[str, Callable],
        entry: _Entry,
    ) -> None:
        self._store = store
        self._fabric_type = fabric_type
        self._scope_tags = scope_tags
        self._predicates = predicates
        self._entry = entry
        self._restore: Callable[[], None] | None = None

    def __enter__(self) -> None:
        self._restore = self._store._put(
            self._fabric_type, self._scope_tags, self._predicates, self._entry
        )

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._restore is not None:
            self._restore()
            self._restore = None


def _subsets_of_size(items: list, size: int) -> Generator[tuple, None, None]:
    """Generate all subsets of a given size from items."""
    if size == 0:
        yield ()
        return
    for i in range(len(items)):
        for rest in _subsets_of_size(items[i + 1 :], size - 1):
            yield (items[i], *rest)
