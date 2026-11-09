"""Whole-container read for kv refs: the value, or NULL where nothing is written.

A kv container ref reads as a lazy View, never NULL, so the one value read is
``extract()``. Virtuals raises its own not-found error when the container was
never written; this atom turns exactly that into NULL hinted with the ref's
dotted path, so the core ``Extract`` never meets virtuals' own markers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
from nu.lang import ScalarQuery
from nu.lang.null import Null
from virtuals.container import ContainerNotFoundError
from virtuals.view import Faceted


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime
    from nustd.kv.refs.base import ViewRef
    from virtuals.view import ViewBase


__all__ = [
    "ViewExtract",
]


def _own_absence(err: ContainerNotFoundError, view: ViewBase) -> bool:
    """Whether ``err`` names the view's own container, not one above or below it."""
    return err.site == view.container.site


def _extractor(ref: ViewRef) -> Callable[[ViewBase], object]:
    """How the fetched view reads out, decided once from the ref's declared view class.

    A view class with facets reads through its eager facet, so nested
    containers come back extracted; any other view extracts as it is.
    """
    view_class = nu.tree.payload(ref).get("type_marker")  # type: ignore[attr-defined]
    if isinstance(view_class, type) and issubclass(view_class, Faceted):
        return lambda view: view.eager.extract()  # type: ignore[attr-defined]
    return lambda view: view.extract()  # type: ignore[attr-defined]


class ViewExtract(ScalarQuery):
    """Reads a kv container's whole subtree as plain Python values.

    Args:
        ref: the container Ref to read.

    Notes:
        - NULL, hinted with the dotted path, when the container was never
          written. A container written empty reads as its empty value.
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
        extract = _extractor(ref)

        def thunk(rt: Runtime) -> object:
            view = ref_thunk(rt)
            try:
                return extract(view)
            except ContainerNotFoundError as err:
                if not _own_absence(err, view):
                    raise
                path = ref._resolve_path(rt, rt.program.children[nid][0])
                return Null(ref._hint(path))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        ref_thunk = children[0]
        extract = _extractor(ref)

        async def athunk(rt: Runtime) -> object:
            view = await ref_thunk(rt)
            try:
                return extract(view)
            except ContainerNotFoundError as err:
                if not _own_absence(err, view):
                    raise
                path = await ref._aresolve_path(rt, rt.program.children[nid][0])
                return Null(ref._hint(path))

        return athunk
