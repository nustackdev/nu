"""Backend fixtures: every compliance test runs once per backend.

The fixtures live in ``_support.blob_fixtures``, shared with the blob serving
tests in ``tests/nustd/ui``.
"""

from __future__ import annotations

from _support.blob_fixtures import backend, kind, moto_s3, store_path


__all__ = ["backend", "kind", "moto_s3", "store_path"]
