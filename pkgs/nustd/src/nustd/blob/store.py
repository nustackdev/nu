"""StoreRef: a named blob store, the Ref every blob term reaches its backend through."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu.context import FabricRef
from nu.lang import Nu, ScalarQuery
from nu.lang.null import Null, is_null

from ._base import check_id
from .fabric import BlobFabric
from .interactions import (
    BlobDelete,
    BlobGet,
    BlobHas,
    BlobMeta,
    BlobNewId,
    BlobOpen,
    BlobPut,
    BlobPutStream,
)
from .protocol import STEP


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.forms import Iterator
    from nu.forms.primitives import Bool
    from nu.lang import IntArg, StrArg
    from nu.lang.runtime import Runtime


__all__ = ["StoreRef", "store_name"]


def store_name(store: object) -> str | Nu:
    """The store's name: a ``StoreRef``'s name term, a non-empty ``str``, or a term computing it.

    A term is returned as given, never looked into; its value is checked when it
    is evaluated.
    """
    if isinstance(store, StoreRef):
        return store.name
    if isinstance(store, Nu):
        return store
    if isinstance(store, str) and store:
        return store
    raise TypeError(f"a blob store is a StoreRef or its name, a non-empty str, got {store!r}")


class StoreRef(FabricRef):
    """A named blob store: the ``BlobFabric`` bound under its name, and the terms that reach it.

    The name is the tag a backend binds under, so several stores live in one
    tree without meeting. Every term holds this ref itself, so one
    ``StoreRef`` held in a module serves any number of terms and trees.

    Args:
        name: the store's name, any non-empty ``str``, or a term yielding
            one, evaluated each time the ref is read.

    Notes:
        - Reading it is a lookup and nothing else: the bound ``BlobFabric``,
          or NULL when nothing is bound under the name. Every blob atom takes
          it in slot 0 and does the work itself; it is also the Ref the two
          mutating atoms land their write through.
        - ``exists()`` asks whether a backend is bound; ``has(id)`` asks
          whether a blob is stored.
        - The store knows nothing about urls. Serving a store over http is
          the web layer's, which says where (``nustd.blob.http.BlobMount``).

    Yields:
        The bound ``BlobFabric``, or NULL when nothing is bound for the name.

    Example:
        Media = nustd.blob.StoreRef("media")

        app = nu.With(
            nustd.blob.lmdb(Media, ".store/media"),
            body=nu.let(Media.put(b"..."), lambda bid: Media.get(bid)),
        )
    """

    fabric = BlobFabric

    def __init__(self, name: str | Nu) -> None:
        # Children: [fabric, name]. A plain name is checked here, a computed
        # one each time it is evaluated.
        super().__init__(None, store_name(name))

    @property
    def name(self) -> Nu:
        """The store's name, the tag its backend binds under: the name child, a term."""
        return self._children[1]

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric, name_of = children[0], children[1]

        def thunk(rt: Runtime) -> object:
            f = fabric(rt)
            name = cast("str", store_name(name_of(rt)))
            if rt.ctx.fabrics.has(f, name):
                return rt.ctx.fabrics.get(f, name)
            return Null(name)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric, name_of = children[0], children[1]

        async def athunk(rt: Runtime) -> object:
            f = await fabric(rt)
            name = cast("str", store_name(await name_of(rt)))
            if rt.ctx.fabrics.has(f, name):
                return rt.ctx.fabrics.get(f, name)
            return Null(name)

        return athunk

    # --- terms --------------------------------------------------------------

    def put(
        self,
        source: object,
        *,
        blob_id: StrArg | None = None,
        mime: StrArg = "",
        name: StrArg = "",
    ) -> BlobPut:
        """Store bytes once and yield the new id; see ``BlobPut``.

        Args:
            source: bytes, a ``Path``, a binary file or an iterable of bytes;
                under an async run also an async iterable. Not a stream term:
                put one with ``put_stream``.
            blob_id: an id minted earlier, by ``new_id``; None mints at run
                time.
            mime: the media type the bytes are served as.
            name: the file name a download offers.
        """
        _check_given_id(blob_id)
        return BlobPut(self, source, blob_id, mime, name)

    def put_stream(
        self,
        source: object,
        *,
        blob_id: StrArg | None = None,
        mime: StrArg = "",
        name: StrArg = "",
    ) -> BlobPutStream:
        """Store a stream of byte pieces once and yield the new id; see ``BlobPutStream``.

        Args:
            source: a stream term of ``bytes`` pieces, such as another store's
                ``open``; the pieces reach the store as they are pulled.
            blob_id: an id minted earlier, by ``new_id``; None mints at run
                time.
            mime: the media type the bytes are served as.
            name: the file name a download offers.
        """
        _check_given_id(blob_id)
        return BlobPutStream(self, source, blob_id, mime, name)

    def new_id(self) -> BlobNewId:
        """A fresh id, minted at run time, for a put inside a block that can retry."""
        return BlobNewId(self)

    def get(self, blob_id: StrArg) -> BlobGet:
        """The blob's bytes, whole."""
        _check_given_id(blob_id)
        return BlobGet(self, blob_id)

    def open(
        self,
        blob_id: StrArg,
        start: IntArg = 0,
        end: IntArg | None = None,
        step: IntArg = STEP,
    ) -> Iterator:
        """A range of the blob as a lazy stream of byte pieces; see ``BlobOpen``.

        Args:
            blob_id: the blob's id.
            start: the first byte, from 0.
            end: one past the last byte; None for the end of the blob.
            step: bytes per piece.
        """
        from nu.forms import Iterator

        _check_given_id(blob_id)
        return Iterator(BlobOpen(self, blob_id, start, end, step))

    def meta(self, blob_id: StrArg) -> BlobMeta:
        """The blob's ``{id, size, mime, name, created_at}``."""
        _check_given_id(blob_id)
        return BlobMeta(self, blob_id)

    def has(self, blob_id: StrArg) -> BlobHas:
        """Whether a whole blob sits under the id."""
        _check_given_id(blob_id)
        return BlobHas(self, blob_id)

    def delete(self, blob_id: StrArg) -> BlobDelete:
        """Remove the blob; a missing one is a no-op."""
        _check_given_id(blob_id)
        return BlobDelete(self, blob_id)

    def exists(self) -> Bool:
        """Whether a backend is bound under this store's name, as a ``Bool``.

        Notes:
            - Overrides the base check, which looks only at the untagged
              binding: a store's backend is always bound under its name.
        """
        from nu.forms.primitives import Bool

        return Bool(_StoreBound(self))


def _check_given_id(blob_id: object) -> None:
    """Refuse a malformed id when the tree is built; a term's id is checked when it runs."""
    if isinstance(blob_id, str):
        check_id(blob_id)


class _StoreBound(ScalarQuery):
    """Whether its ``StoreRef`` reads a bound backend rather than NULL.

    Args:
        ref: the ``StoreRef`` to read.

    Yields:
        True or False.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref,) = children

        def thunk(rt: Runtime) -> bool:
            return not is_null(ref(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref,) = children

        async def athunk(rt: Runtime) -> bool:
            return not is_null(await ref(rt))

        return athunk
