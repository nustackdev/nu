"""The blob interactions: put, put a stream, mint, read whole, stream, meta, has, delete.

Slot 0 of every atom is the store: a ``StoreRef`` yielding the ``BlobFabric``
bound under the store's name. Everything else is a child, so an id, a range
or a source can come from any term, such as the id a put earlier in the same
program yielded.

=============  ====================================  ===============  =======
atom           slots                                 sort             mutates
=============  ====================================  ===============  =======
BlobPut        (store, source, blob_id, mime, name)  ScalarAction     {0}
BlobPutStream  (store, source, blob_id, mime, name)  ActionReduction  {0}
BlobNewId      (store,)                              ScalarQuery      -
BlobGet        (store, blob_id)                      ScalarQuery      -
BlobOpen       (store, blob_id, start, end, step)    StreamQuery      -
BlobMeta       (store, blob_id)                      ScalarQuery      -
BlobHas        (store, blob_id)                      ScalarQuery      -
BlobDelete     (store, blob_id)                      Command          {0}
=============  ====================================  ===============  =======

``BlobPut`` takes one value as its source. ``BlobPutStream`` takes a stream
term in that slot, such as another store's ``open``, and folds it into one
write: the pieces go straight to the backend as they are pulled, never
collected.

A sync run calls the backend's sync methods, an async run its async twins, so
no blob call blocks the event loop.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ActionReduction, Command, Nu, ScalarAction, ScalarQuery, StreamQuery
from nu.lang._stream import aiter_any, sync_iter
from nu.lang.null import is_null

from ._base import new_id
from .fabric import BlobFabric
from .protocol import STEP


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import IntArg, StrArg
    from nu.lang.runtime import Runtime

    from .protocol import AsyncSource, BlobBackend


__all__ = [
    "BlobDelete",
    "BlobGet",
    "BlobHas",
    "BlobMeta",
    "BlobNewId",
    "BlobOpen",
    "BlobPut",
    "BlobPutStream",
]


# --- child helpers ----------------------------------------------------------


def _store_node(store: object) -> Nu:
    """The store slot, a term such as a ``StoreRef``; anything else is refused."""
    if not isinstance(store, Nu):
        msg = (
            f"the store slot is a term, such as a StoreRef, got {store!r}: "
            "build blob terms from the store, as store.get(blob_id)"
        )
        raise TypeError(msg)
    return store


def _backend(value: object) -> BlobBackend:
    """The open backend behind the store slot's value; NULL means nothing was bound."""
    if is_null(value) or value is None:
        hint = f" for {value.hint}" if is_null(value) and value.hint else ""
        msg = (
            f"no blob backend is bound{hint}: wrap the tree in "
            "nu.With(nustd.blob.lmdb(store, path), body=...) or nustd.blob.files(...)"
        )
        raise RuntimeError(msg)
    if not isinstance(value, BlobFabric):
        raise TypeError(f"the store slot yielded {type(value).__name__}, not a BlobFabric")
    return value.backend


def _optional(value: object) -> object:
    """A child that may be left out: NULL reads as None."""
    return None if is_null(value) else value


# --- write ------------------------------------------------------------------


class BlobPut(ScalarAction):
    """Stores bytes once under a fresh id and yields the id.

    Args:
        store: the store slot, a ``StoreRef``.
        source: bytes, a ``Path``, a binary file or an iterable of bytes; under
            an async run also an async iterable. A ``str`` is refused.
        blob_id: the id to store under. None mints one when the put runs.
        mime: the media type a reader serves the bytes as.
        name: the file name a download offers.

    Notes:
        - The id is minted at run time, never when the tree is built, so a
          tree run twice stores twice under two ids.
        - Inside a block that can retry, mint first with ``BlobNewId`` and
          pass the id: a retry then raises ``BlobExists`` rather than leaving
          a second copy behind.
        - A file or an iterable spools to the store's disk first and is never
          held whole in memory.
        - The source is one value: a stream term, such as another store's
          ``open``, is refused by the tree's checks. Put a stream with
          ``BlobPutStream`` (``store.put_stream``), which feeds the pieces
          to the store as they come, so a copy between stores is
          ``B.put_stream(A.open(bid))``.

    Yields:
        The id, a 32 character hex ``str``. ``BlobMeta`` gives the rest.

    Example:
        bid = Media.put(Path("cat.png"), mime="image/png", name="cat.png")
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(
        self,
        store: object,
        source: object,
        blob_id: StrArg | None = None,
        mime: StrArg = "",
        name: StrArg = "",
    ) -> None:
        super().__init__(_store_node(store), source, blob_id, mime, name)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, source, blob_id, mime, name = children

        def thunk(rt: Runtime) -> str:
            backend = _backend(store(rt))
            info = backend.put(
                source(rt),
                blob_id=_optional(blob_id(rt)),  # type: ignore[arg-type]
                mime=mime(rt),
                name=name(rt),
            )
            return info.id

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, source, blob_id, mime, name = children

        async def athunk(rt: Runtime) -> str:
            backend = _backend(await store(rt))
            data: AsyncSource = await source(rt)
            info = await backend.aput(
                data,
                blob_id=_optional(await blob_id(rt)),  # type: ignore[arg-type]
                mime=await mime(rt),
                name=await name(rt),
            )
            return info.id

        return athunk


class BlobPutStream(ActionReduction):
    """Stores a stream of byte pieces once under a fresh id and yields the id.

    Args:
        store: the store slot, a ``StoreRef``.
        source: a stream term of ``bytes`` pieces, such as another store's
            ``open`` or an upload's stream. A scalar is refused by the tree's
            checks: put one value with ``BlobPut``.
        blob_id: the id to store under. None mints one when the put runs.
        mime: the media type a reader serves the bytes as.
        name: the file name a download offers.

    Notes:
        - A reduction: slot 1 takes the stream and the put folds it into one
          write. Every other slot is one value.
        - The pieces go straight to the backend as they are pulled, which
          spools them to the store's disk; the whole blob is never held in
          memory.
        - Id, mime and name work as in ``BlobPut``, retries included.

    Yields:
        The id, a 32 character hex ``str``.

    Example:
        bid = Media.put_stream(Archive.open(old_id), mime="image/png")
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _reduces = Declared(value=1, name="reduces")

    def __init__(
        self,
        store: object,
        source: object,
        blob_id: StrArg | None = None,
        mime: StrArg = "",
        name: StrArg = "",
    ) -> None:
        super().__init__(_store_node(store), source, blob_id, mime, name)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, source, blob_id, mime, name = children

        def thunk(rt: Runtime) -> str:
            backend = _backend(store(rt))
            info = backend.put(
                sync_iter(source(rt)),
                blob_id=_optional(blob_id(rt)),  # type: ignore[arg-type]
                mime=mime(rt),
                name=name(rt),
            )
            return info.id

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, source, blob_id, mime, name = children

        async def athunk(rt: Runtime) -> str:
            backend = _backend(await store(rt))
            info = await backend.aput(
                aiter_any(await source(rt)),
                blob_id=_optional(await blob_id(rt)),  # type: ignore[arg-type]
                mime=await mime(rt),
                name=await name(rt),
            )
            return info.id

        return athunk


class BlobNewId(ScalarQuery):
    """A fresh blob id, minted when it runs.

    Args:
        store: the store slot, a ``StoreRef``.

    Notes:
        - For a put inside a block that can retry: mint outside it, put with
          ``blob_id=`` inside, and a retry finds ``BlobExists`` instead of
          leaving a second copy.
        - Nothing is reserved: the id is free until a put takes it.

    Yields:
        A new id, a 32 character hex ``str``.

    Example:
        nu.let(Media.new_id(), lambda bid: Media.put(data, blob_id=bid))
    """

    def __init__(self, store: object) -> None:
        super().__init__(_store_node(store))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (store,) = children

        def thunk(rt: Runtime) -> str:
            _backend(store(rt))
            return new_id()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (store,) = children

        async def athunk(rt: Runtime) -> str:
            _backend(await store(rt))
            return new_id()

        return athunk


# --- read -------------------------------------------------------------------


class BlobGet(ScalarQuery):
    """The bytes of a blob, whole.

    Args:
        store: the store slot, a ``StoreRef``.
        blob_id: the blob's id.

    Notes:
        - The whole value sits in memory: stream a big blob with ``BlobOpen``.
        - An unknown id raises ``BlobNotFound``.

    Yields:
        The blob's bytes.

    Example:
        Media.get(bid)
    """

    def __init__(self, store: object, blob_id: StrArg) -> None:
        super().__init__(_store_node(store), blob_id)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id = children

        def thunk(rt: Runtime) -> bytes:
            return _backend(store(rt)).read(blob_id(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id = children

        async def athunk(rt: Runtime) -> bytes:
            backend = _backend(await store(rt))
            return await backend.aread(await blob_id(rt))

        return athunk


class BlobOpen(StreamQuery):
    """The bytes of a range of a blob, a piece at a time (lazy).

    Args:
        store: the store slot, a ``StoreRef``.
        blob_id: the blob's id.
        start: the first byte, from 0.
        end: one past the last byte; None for the end of the blob. The range
            clamps to the blob's size.
        step: bytes per piece; the last piece may be shorter.

    Notes:
        - Pulled lazily: each pull reads one piece from the backend, and
          nothing runs ahead of the pull. An async run reads each piece in a
          thread.
        - An unknown id raises ``BlobNotFound`` at the first pull.
        - The backend must stay bound while the stream is drained: drain it
          inside the ``With`` that binds the store.

    Yields:
        A stream of ``bytes`` pieces, in order, that join to the range.

    Example:
        nu.Collect(Media.open(bid, 0, 1 << 20))
    """

    def __init__(
        self,
        store: object,
        blob_id: StrArg,
        start: IntArg = 0,
        end: IntArg | None = None,
        step: IntArg = STEP,
    ) -> None:
        super().__init__(_store_node(store), blob_id, start, end, step)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id, start, end, step = children

        def thunk(rt: Runtime) -> object:
            backend = _backend(store(rt))
            return backend.stream(
                blob_id(rt),
                start(rt),
                _optional(end(rt)),  # type: ignore[arg-type]
                step=step(rt),
            )

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id, start, end, step = children

        async def athunk(rt: Runtime) -> object:
            backend = _backend(await store(rt))
            return backend.astream(
                await blob_id(rt),
                await start(rt),
                _optional(await end(rt)),  # type: ignore[arg-type]
                step=await step(rt),
            )

        return athunk


class BlobMeta(ScalarQuery):
    """What a blob is, apart from its bytes.

    Args:
        store: the store slot, a ``StoreRef``.
        blob_id: the blob's id.

    Notes:
        - An unknown id raises ``BlobNotFound``.

    Yields:
        A dict: ``id``, ``size`` in bytes, ``mime``, ``name`` and
        ``created_at`` in epoch seconds.

    Example:
        Media.meta(bid)
    """

    def __init__(self, store: object, blob_id: StrArg) -> None:
        super().__init__(_store_node(store), blob_id)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id = children

        def thunk(rt: Runtime) -> dict[str, object]:
            return _backend(store(rt)).info(blob_id(rt)).to_dict()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id = children

        async def athunk(rt: Runtime) -> dict[str, object]:
            backend = _backend(await store(rt))
            return (await backend.ainfo(await blob_id(rt))).to_dict()

        return athunk


class BlobHas(ScalarQuery):
    """Whether a whole blob sits under an id.

    Named ``Has``, not ``Exists``: ``BlobExists`` is the error a put raises
    on a taken id.

    Args:
        store: the store slot, a ``StoreRef``.
        blob_id: the id to look for.

    Yields:
        A ``bool``.

    Example:
        Media.has(bid)
    """

    def __init__(self, store: object, blob_id: StrArg) -> None:
        super().__init__(_store_node(store), blob_id)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id = children

        def thunk(rt: Runtime) -> bool:
            return _backend(store(rt)).exists(blob_id(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id = children

        async def athunk(rt: Runtime) -> bool:
            backend = _backend(await store(rt))
            return await backend.aexists(await blob_id(rt))

        return athunk


# --- remove -----------------------------------------------------------------


class BlobDelete(Command):
    """Removes a blob.

    Args:
        store: the store slot, a ``StoreRef``.
        blob_id: the blob's id.

    Notes:
        - An id with no blob is a no-op, so a delete can safely run twice.
        - Caches keep serving the old bytes under the id's url, so never put
          new bytes under a deleted id.

    Example:
        Media.delete(bid)
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, store: object, blob_id: StrArg) -> None:
        super().__init__(_store_node(store), blob_id)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id = children

        def thunk(rt: Runtime) -> None:
            _backend(store(rt)).delete(blob_id(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        store, blob_id = children

        async def athunk(rt: Runtime) -> None:
            backend = _backend(await store(rt))
            await backend.adelete(await blob_id(rt))

        return athunk
