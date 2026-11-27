"""Blob backends: plain Python stores behind ``BlobBackend``, no Nu.

- ``LMDBBackend``: one LMDB env, a blob cut into chunks under its id (needs ``nustd[blob]``).
- ``FilesBackend``: a file per id in a directory tree, appended in place.
- ``S3Backend``: an object per id in an S3 bucket (needs ``nustd[blob_s3]``).
"""

from __future__ import annotations

from .files import FilesBackend
from .lmdb import LMDBBackend
from .s3 import S3Backend


__all__ = ["FilesBackend", "LMDBBackend", "S3Backend"]
