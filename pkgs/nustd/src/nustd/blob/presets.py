"""lmdb(), files() and s3(): bind a backend under a store's name for the span of a tree."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from nu.context import Provide

from .backends import FilesBackend, LMDBBackend, S3Backend
from .backends.lmdb import DEFAULT_MAP_SIZE, DEFAULT_MAX_READERS, DEFAULT_WRITEMAP
from .backends.s3 import DEFAULT_PART_SIZE
from .fabric import BlobFabric
from .store import store_name


if TYPE_CHECKING:
    from .store import StoreRef


__all__ = ["files", "lmdb", "s3"]


def lmdb(
    store: StoreRef | str,
    path: str | os.PathLike[str],
    *,
    map_size: int = DEFAULT_MAP_SIZE,
    max_readers: int = DEFAULT_MAX_READERS,
    writemap: bool = DEFAULT_WRITEMAP,
) -> Provide:
    """Give a store an LMDB env at ``path``, open while the tree runs.

    Args:
        store: the store the backend binds under, its ``StoreRef`` or its name.
        path: the env directory, made on first open. Local disk only, never
            NFS.
        map_size: bytes of address space; the env cannot grow past it while
            open.
        max_readers: reader slots shared by every process on the env.
        writemap: put straight into the map rather than through C heap
            pages. On by default on Linux, off on macOS, where each commit
            costs time in proportion to ``map_size``; see ``LMDBBackend``.

    Notes:
        - Runs in one process that bind the same path share one open env,
          so they may overlap. They must agree on ``map_size``,
          ``max_readers`` and ``writemap``, or the later one raises.
        - Workers that open the same path must be started with ``spawn``.

    Example:
        nu.With(nustd.blob.lmdb(Media, ".store/media"), body=Media.put(b"..."))
    """
    options = {
        "path": os.fspath(path),
        "map_size": map_size,
        "max_readers": max_readers,
        "writemap": writemap,
    }
    return Provide(
        BlobFabric, kwargs={"backend": LMDBBackend, "options": options}, tag=store_name(store)
    )


def files(store: StoreRef | str, root: str | os.PathLike[str]) -> Provide:
    """Give a store a directory of plain files at ``root``, one file per blob.

    Args:
        store: the store the backend binds under, its ``StoreRef`` or its name.
        root: the tree's root, made on first open.

    Example:
        nu.With(nustd.blob.files(Media, "./media"), body=Media.put(b"..."))
    """
    options = {"root": os.fspath(root)}
    return Provide(
        BlobFabric, kwargs={"backend": FilesBackend, "options": options}, tag=store_name(store)
    )


def s3(
    store: StoreRef | str,
    *,
    bucket: str,
    prefix: str = "",
    endpoint_url: str | None = None,
    region_name: str | None = None,
    profile_name: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    aws_session_token: str | None = None,
    part_size: int = DEFAULT_PART_SIZE,
) -> Provide:
    """Give a store a bucket of any S3-compatible service, one object per blob.

    Args:
        store: the store the backend binds under, its ``StoreRef`` or its name.
        bucket: the bucket, made beforehand.
        prefix: put before every id to make its key; end it with ``/`` for a
            folder.
        endpoint_url: the service, for anything that is not AWS (R2, MinIO).
        region_name: the region; boto3's own default when None.
        profile_name: an AWS profile to take credentials from.
        aws_access_key_id: a credential for boto3. Keys travel inside the
            tree, to every process it is sent to; leave all three out to let
            boto3 find credentials in each process (env, profile, role).
        aws_secret_access_key: as ``aws_access_key_id``.
        aws_session_token: as ``aws_access_key_id``, for temporary keys.
        part_size: bytes per multipart part, at least 5 MiB. A put holds one
            part in memory, and a blob holds at most 10,000 parts.

    Example:
        nu.With(nustd.blob.s3(Media, bucket="media", prefix="space/"), body=Media.put(b"..."))
    """
    options = {
        "bucket": bucket,
        "prefix": prefix,
        "endpoint_url": endpoint_url,
        "region_name": region_name,
        "profile_name": profile_name,
        "aws_access_key_id": aws_access_key_id,
        "aws_secret_access_key": aws_secret_access_key,
        "aws_session_token": aws_session_token,
        "part_size": part_size,
    }
    return Provide(
        BlobFabric, kwargs={"backend": S3Backend, "options": options}, tag=store_name(store)
    )
