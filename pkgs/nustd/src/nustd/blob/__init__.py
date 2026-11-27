"""Nu blob fabric: append-only bytes under an id, stored and read in streams, readable as they grow.

The fabric stores and returns, nothing else. Serving a store over http is
``nustd.blob.http``'s: ``BlobMount`` says where, ``serve_blobs`` serves.

Surface:
    - StoreRef(name): a named store; its terms are ``put``, ``put_stream``,
      ``append``, ``append_stream``, ``seal``, ``new_id``, ``get``, ``open``,
      ``meta``, ``has``, ``sealed`` and ``delete``, and ``exists()`` asks
      whether a backend is bound.
    - lmdb(store, path), files(store, root), s3(store, bucket=...): bind a
      backend under a store's name for the span of a tree.
    - BlobPut, BlobPutStream, BlobAppend, BlobAppendStream, BlobSeal, BlobNewId,
      BlobGet, BlobOpen, BlobMeta, BlobHas, BlobIsSealed, BlobDelete: the
      interactions those terms build; BlobFabric beneath them.
    - BlobBackend: the protocol every backend keeps, sync plus async twins.
    - BlobInfo, BlobNotFound, BlobExists, BlobSealed, BlobIdle, BlobTooLarge:
      what calls give and raise.
    - LMDBBackend, FilesBackend, S3Backend: the backends, plain Python, no Nu:
      what code outside a tree takes, such as the server ``serve_blobs`` builds.

Example::

    Media = nustd.blob.StoreRef("media")

    app = nu.With(
        nustd.blob.lmdb(Media, ".store/media"),
        body=nu.let(
            lambda bid: Media.meta(bid),
            bid=Media.put(Path("cat.png"), mime="image/png", name="cat.png"),
        ),
    )

The backends work without Nu too::

    backend = nustd.blob.LMDBBackend("/var/lib/app/blobs")
    backend.open()
    info = backend.put(Path("cat.png"), mime="image/png", name="cat.png")
    head = backend.read(info.id, 0, 1024)
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from .backends import FilesBackend, LMDBBackend, S3Backend
from .protocol import (
    STEP,
    AsyncSource,
    BlobBackend,
    BlobExists,
    BlobIdle,
    BlobInfo,
    BlobNotFound,
    BlobSealed,
    BlobTooLarge,
    Source,
)


if TYPE_CHECKING:
    from . import http
    from .fabric import BlobFabric
    from .interactions import (
        BlobAppend,
        BlobAppendStream,
        BlobDelete,
        BlobGet,
        BlobHas,
        BlobIsSealed,
        BlobMeta,
        BlobNewId,
        BlobOpen,
        BlobPut,
        BlobPutStream,
        BlobSeal,
    )
    from .presets import files, lmdb, s3
    from .store import StoreRef


# The Nu layer loads on first access, so the plain layers stay plain: a
# process that only drives a backend never imports Nu's engine.
_LAZY = {
    "http": "http",
    "BlobAppend": "interactions",
    "BlobAppendStream": "interactions",
    "BlobDelete": "interactions",
    "BlobFabric": "fabric",
    "BlobGet": "interactions",
    "BlobHas": "interactions",
    "BlobIsSealed": "interactions",
    "BlobMeta": "interactions",
    "BlobNewId": "interactions",
    "BlobOpen": "interactions",
    "BlobPut": "interactions",
    "BlobPutStream": "interactions",
    "BlobSeal": "interactions",
    "StoreRef": "store",
    "files": "presets",
    "lmdb": "presets",
    "s3": "presets",
}


def __getattr__(name: str) -> object:
    """Load a Nu layer name on first access."""
    if name not in _LAZY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f".{_LAZY[name]}", __name__)
    value = module if name == "http" else getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *_LAZY})


__all__ = [
    "STEP",
    "AsyncSource",
    "BlobAppend",
    "BlobAppendStream",
    "BlobBackend",
    "BlobDelete",
    "BlobExists",
    "BlobFabric",
    "BlobGet",
    "BlobHas",
    "BlobIdle",
    "BlobInfo",
    "BlobIsSealed",
    "BlobMeta",
    "BlobNewId",
    "BlobNotFound",
    "BlobOpen",
    "BlobPut",
    "BlobPutStream",
    "BlobSeal",
    "BlobSealed",
    "BlobTooLarge",
    "FilesBackend",
    "LMDBBackend",
    "S3Backend",
    "Source",
    "StoreRef",
    "files",
    "http",
    "lmdb",
    "s3",
]
