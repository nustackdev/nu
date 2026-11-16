"""Nu blob fabric: write-once bytes under an id, stored and read in streams.

The fabric stores and returns, nothing else. Serving a store over http is
``nustd.blob.http``'s: ``BlobMount`` says where, ``serve_blobs`` serves.

Surface:
    - StoreRef(name): a named store; its terms are ``put``, ``new_id``,
      ``get``, ``open``, ``meta``, ``has`` and ``delete``, and ``exists()``
      asks whether a backend is bound.
    - lmdb(store, path), files(store, root), s3(store, bucket=...): bind a
      backend under a store's name for the span of a tree.
    - backend_of(spec): the backend such a binding builds, for use outside a
      tree, unopened.
    - BlobPut, BlobNewId, BlobGet, BlobOpen, BlobMeta, BlobHas, BlobDelete:
      the interactions those terms build; BlobFabric beneath them.
    - BlobBackend: the protocol every backend keeps, sync plus async twins.
    - BlobInfo, BlobNotFound, BlobExists, BlobTooLarge: what calls give and raise.
    - LMDBBackend, FilesBackend, S3Backend: the backends, plain Python, no Nu.

Example::

    Media = nustd.blob.StoreRef("media")

    app = nu.With(
        nustd.blob.lmdb(Media, ".store/media"),
        body=nu.let(
            Media.put(Path("cat.png"), mime="image/png", name="cat.png"),
            lambda bid: Media.meta(bid),
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
    BlobInfo,
    BlobNotFound,
    BlobTooLarge,
    Source,
)


if TYPE_CHECKING:
    from .fabric import BlobFabric
    from .interactions import (
        BlobDelete,
        BlobGet,
        BlobHas,
        BlobMeta,
        BlobNewId,
        BlobOpen,
        BlobPut,
    )
    from .presets import backend_of, files, lmdb, s3
    from .store import StoreRef


# The Nu layer loads on first access, so the plain layers stay plain: a
# process that only drives a backend never imports Nu's engine.
_LAZY = {
    "http": "http",
    "BlobDelete": "interactions",
    "BlobFabric": "fabric",
    "BlobGet": "interactions",
    "BlobHas": "interactions",
    "BlobMeta": "interactions",
    "BlobNewId": "interactions",
    "BlobOpen": "interactions",
    "BlobPut": "interactions",
    "StoreRef": "store",
    "backend_of": "presets",
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
    "BlobBackend",
    "BlobDelete",
    "BlobExists",
    "BlobFabric",
    "BlobGet",
    "BlobHas",
    "BlobInfo",
    "BlobMeta",
    "BlobNewId",
    "BlobNotFound",
    "BlobOpen",
    "BlobPut",
    "BlobTooLarge",
    "FilesBackend",
    "LMDBBackend",
    "S3Backend",
    "Source",
    "StoreRef",
    "backend_of",
    "files",
    "lmdb",
    "s3",
]
