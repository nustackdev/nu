"""Shared base for the Parallel / Race / AnyN kinds.

Owns the ``(child, "threaded"|"async")`` tuple-parsing constructor and the
class-level ``_FORCE_MODE`` slot the Threaded/Async variants override.
Compile-time laws that reject a forced-mode variant sitting over a subtree
with the wrong async-affinity fold live in ``nu.lang.laws.parallel`` -
kept there so ``nu.lang.laws`` never imports from ``nu.flows`` and no
cycle forms during ``nu.lang`` initialization.
"""

from __future__ import annotations

from nu.lang.nu import Nu


__all__ = ["_ParallelBase"]


_VALID_MODES = ("threaded", "async")


class _ParallelBase(Nu):
    """Mixin for Parallel / Race / AnyN and their forced-mode variants.

    Args:
        *items: each item is a ``Nu`` child, or a ``(child, "threaded" |
            "async")`` tuple pinning that one child's placement.

    Notes:
        - Parses ``items`` into children plus a per-slot mode tuple stored on
          ``self._payload["parallel_modes"]``, one entry per child (``None``
          for an unpinned child).
        - ``_FORCE_MODE`` is ``None`` on the smart kinds; the
          Threaded/Async subclasses set it to ``"threaded"`` / ``"async"``
          to pin every child at once, overriding per-child modes.
    """

    _FORCE_MODE: str | None = None

    def __init__(self, *items: object) -> None:
        children: list[Nu] = []
        modes: list[str | None] = []
        for item in items:
            if isinstance(item, tuple):
                if len(item) != 2 or not isinstance(item[0], Nu):
                    msg = (
                        f"Parallel child override must be (child, 'threaded'|'async'); got {item!r}"
                    )
                    raise TypeError(msg)
                child, mode = item
                if not isinstance(mode, str) or mode not in _VALID_MODES:
                    msg = f"Parallel child mode must be 'threaded' or 'async'; got {mode!r}"
                    raise ValueError(msg)
                children.append(child)
                modes.append(mode)
            elif isinstance(item, Nu):
                children.append(item)
                modes.append(None)
            else:
                msg = (
                    f"{type(self).__name__} child must be a Nu instance or "
                    f"(Nu, 'threaded'|'async') tuple; got {item!r}"
                )
                raise TypeError(msg)
        super().__init__(*children)
        self._payload["parallel_modes"] = tuple(modes)
