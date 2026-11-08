"""Whole-container read for kv refs: the value, or NULL where nothing is written.

A kv container ref reads as a lazy View, never NULL, so the one value read is
``extract()``. Virtuals raises its own not-found error when the container was
never written; this atom turns exactly that into NULL hinted with the ref's
dotted path, so the core ``Extract`` never meets virtuals' own markers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.null import Null, is_null
from virtuals.container import ContainerNotFoundError


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "ViewExtract",
]


def _own_absence(err: ContainerNotFoundError, view: object) -> bool:
    """Whether ``err`` names the view's own container, not one below it."""
    site = getattr(err, "site", None)
    own = getattr(getattr(view, "container", None), "site", None)
    return site is None or own is None or site == own


def _extract(view: object) -> object:
    if hasattr(view, "eager"):
        view = view.eager
    return view.extract()  # type: ignore[attr-defined]


class ViewExtract(ScalarQuery):
    """Reads a kv container's whole subtree as plain Python values.

    Args:
        ref: the container Ref to read.

    Notes:
        - NULL, hinted with the dotted path, when the container was never
          written, or a key in its path read NULL. A container written empty
          reads as its empty value.
        - Nested containers come back extracted, whatever the ref's facet.
        - Any other storage error is let out.

    Yields:
        A dict, list, set or other plain value, or NULL.

    Example:
        run(Portfolio.tags.extract(), ctx)
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        ref_thunk = children[0]

        def thunk(rt: Runtime) -> object:
            view = ref_thunk(rt)
            if is_null(view):
                return view
            try:
                return _extract(view)
            except ContainerNotFoundError as err:
                if not _own_absence(err, view):
                    raise
                path = ref._resolve_path(rt, rt.program.children[nid][0])
                return Null(ref._hint(path))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        ref_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            view = await ref_thunk(rt)
            if is_null(view):
                return view
            try:
                return _extract(view)
            except ContainerNotFoundError as err:
                if not _own_absence(err, view):
                    raise
                path = await ref._aresolve_path(rt, rt.program.children[nid][0])
                return Null(ref._hint(path))

        return athunk
