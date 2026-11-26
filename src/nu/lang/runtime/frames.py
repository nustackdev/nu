"""Frames: the immutable stack behind a Context, and the lookup over it.

Execution resources (storage, RPC clients, sessions, mem dicts, ...) are bound
on a Context keyed by fabric type plus optional scope tags and predicate
guards. Every binding is a frame: one entry and a pointer to the frame below.
A frame is never changed after it is made, so a Context is a pointer to its
top frame and pushing one returns a new Context.

Lookup gives the result a flat table would: per key (type plus tags, plus the
predicate set for a guarded entry) the nearest frame wins, and across keys
the rules are the usual ones: exact tags, then subset fallback, then
untagged, predicates evaluated against the ``**data`` passed to ``get``.
Nesting shadows a key and never reroutes a tagged lookup.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Generator


__all__: list[str] = []


def _name(tag: object) -> str:
    """Human-readable name for a tag."""
    return getattr(tag, "__name__", None) or repr(tag)


# ---------------------------------------------------------------------------
# Entries: the atoms of a frame
# ---------------------------------------------------------------------------


class _Entry:
    """One binding: eager (value) or lazy (factory, built once on first lookup).

    A lazy entry is built under a lock, so concurrent first lookups call the
    factory once, and the value is cached in the entry, which lives in the
    frame that declared it.
    """

    __slots__ = ("_factory", "_lock", "_resolved", "_value", "_was_lazy")

    _value: object
    _factory: Callable[[], object] | None
    _lock: threading.Lock | None
    _resolved: bool
    _was_lazy: bool

    @staticmethod
    def eager(value: object) -> _Entry:
        """Create an eager (pre-resolved) entry."""
        e = _Entry.__new__(_Entry)
        e._value = value
        e._factory = None
        e._lock = None
        e._resolved = True
        e._was_lazy = False
        return e

    @staticmethod
    def deferred(factory: Callable[[], object]) -> _Entry:
        """Create a lazy (deferred) entry."""
        e = _Entry.__new__(_Entry)
        e._value = None
        e._factory = factory
        e._lock = threading.Lock()
        e._resolved = False
        e._was_lazy = True
        return e

    def resolve(self) -> object:
        """Return the value, calling the factory once on first access if lazy."""
        if not self._resolved:
            with self._lock:  # type: ignore[union-attr]  # a lazy entry has one
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


class _Frame:
    """One immutable binding on the stack, and the frame below it."""

    __slots__ = ("entry", "fabric_type", "parent", "predicates", "scope_tags")

    def __init__(
        self,
        parent: _Frame | None,
        fabric_type: object,
        scope_tags: frozenset,
        predicates: dict[str, Callable],
        entry: _Entry,
    ) -> None:
        self.parent = parent
        self.fabric_type = fabric_type
        self.scope_tags = scope_tags
        self.predicates = predicates
        self.entry = entry

    def matches(self, data: dict) -> bool:
        """True if all predicates pass with the given data kwargs."""
        return all(pred(**data) for pred in self.predicates.values())

    def label(self) -> str:
        """The frame as ``Type+tag+...`` for a repr."""
        labels = [_name(self.fabric_type), *(_name(t) for t in self.scope_tags)]
        if self.predicates:
            labels.append("+".join(self.predicates))
        if self.entry.is_lazy:
            labels.append("lazy")
        return "+".join(labels)


# ---------------------------------------------------------------------------
# The merged view of one fabric type
# ---------------------------------------------------------------------------


def _view(top: _Frame | None, fabric_type: object) -> tuple[dict[frozenset, _Entry], list[_Frame]]:
    """Every live binding of ``fabric_type``: the nearest per key, as a flat table would hold.

    Returns the plain entries by scope tags, and the guarded frames outermost
    first (the order they were bound in), each the nearest of its key.
    """
    plain: dict[frozenset, _Entry] = {}
    guarded: list[_Frame] = []
    seen: set[tuple] = set()
    frame = top
    while frame is not None:
        if frame.fabric_type == fabric_type:
            if frame.predicates:
                key = (frame.scope_tags, frozenset(frame.predicates.items()))
                if key not in seen:
                    seen.add(key)
                    guarded.append(frame)
            elif frame.scope_tags not in plain:
                plain[frame.scope_tags] = frame.entry
        frame = frame.parent
    guarded.reverse()
    return plain, guarded


def _find_at(
    plain: dict[frozenset, _Entry], guarded: list[_Frame], scope_tags: frozenset, data: dict
) -> _Entry | None:
    """The entry at exactly ``scope_tags``, or None.

    With data, guarded entries at this level are evaluated: all predicates
    on one must pass (AND), the first passing one wins (OR across them), and
    when guarded entries exist at this level none of the plain one is used.
    """
    if data and guarded:
        candidates = [g for g in guarded if g.scope_tags == scope_tags]
        if candidates:
            for g in candidates:
                if g.matches(data):
                    return g.entry
            return None
    return plain.get(scope_tags)


def _find(
    top: _Frame | None, fabric_type: object, scope_tags: frozenset, data: dict
) -> _Entry | None:
    """The most specific entry for ``fabric_type`` + ``scope_tags``, or None.

    1. Exact scope tags.
    2. Subset fallback: progressively smaller scope tag sets.
    3. The untagged binding.
    """
    plain, guarded = _view(top, fabric_type)
    if not plain and not guarded:
        return None
    entry = _find_at(plain, guarded, scope_tags, data)
    if entry is not None:
        return entry
    if len(scope_tags) > 1:
        tags_list = sorted(scope_tags, key=id)
        for size in range(len(scope_tags) - 1, 0, -1):
            for subset in _subsets_of_size(tags_list, size):
                entry = _find_at(plain, guarded, frozenset(subset), data)
                if entry is not None:
                    return entry
    if scope_tags:
        return _find_at(plain, guarded, frozenset(), data)
    return None


def _missing(fabric_type: object, scope_tags: frozenset, data: dict) -> LookupError:
    """The error a lookup that finds nothing raises."""
    tag_names = ", ".join(_name(t) for t in scope_tags)
    data_str = ", ".join(f"{k}={v!r}" for k, v in data.items())
    parts = [_name(fabric_type)]
    if tag_names:
        parts.append(f"[{tag_names}]")
    if data_str:
        parts.append(f"({data_str})")
    return LookupError(f"No binding for: {''.join(parts)}")


def _subsets_of_size(items: list, size: int) -> Generator[tuple, None, None]:
    """Generate all subsets of a given size from items."""
    if size == 0:
        yield ()
        return
    for i in range(len(items)):
        for rest in _subsets_of_size(items[i + 1 :], size - 1):
            yield (items[i], *rest)
