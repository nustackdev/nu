"""Backend fixtures for every test that drives a blob backend: one run per backend.

Imported by ``tests/nustd/blob/conftest.py`` and by the blob serving tests in
``tests/nustd/ui``. The local backends sit on ``tmp_path``: local disk, as
LMDB must never sit on the NFS repo tree. The s3 one runs on moto, an
in-process S3, with a fresh bucket per test.
"""

from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from nustd.blob import LMDBBackend, S3Backend

from .blob_workers import BUCKET, KINDS, make


__all__ = ["backend", "kind", "leftovers", "moto_s3", "store_path"]


@pytest.fixture
def moto_s3(monkeypatch):
    """An in-process S3 with ``BUCKET`` in it, for the span of a test."""
    for name in ("AWS_PROFILE", "AWS_ENDPOINT_URL", "AWS_ENDPOINT_URL_S3"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        client = boto3.client("s3")
        client.create_bucket(Bucket=BUCKET)
        yield client


@pytest.fixture(params=KINDS)
def kind(request):
    if request.param == "s3":
        request.getfixturevalue("moto_s3")
    return request.param


@pytest.fixture
def store_path(tmp_path):
    return tmp_path / "store"


@pytest.fixture
def backend(kind, store_path):
    backend = make(kind, store_path)
    backend.open()
    yield backend
    backend.close()


def leftovers(backend):
    """What puts left behind that no reader sees, named, sorted.

    Spool files for files; claims and chunks with no meta for lmdb; multipart
    uploads never finished for s3.
    """
    if isinstance(backend, S3Backend):
        listing = backend._client.list_multipart_uploads(
            Bucket=backend.bucket, Prefix=backend.prefix
        )
        return sorted(upload["Key"] for upload in listing.get("Uploads", []))
    if isinstance(backend, LMDBBackend):
        with backend._env.begin() as txn:
            claims = [key.decode() for key, _ in txn.cursor(db=backend._claims)]
            chunked = {key[:16].hex() for key, _ in txn.cursor(db=backend._data)}
            orphans = [bid for bid in chunked if txn.get(bid.encode(), db=backend._meta) is None]
        return sorted({*claims, *orphans})
    return sorted(p.name for p in backend._spool_dir.iterdir())
