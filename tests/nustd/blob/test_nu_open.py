"""Open blobs through the nu terms: put without a seal, append, seal, sealed, and follow.

Run under nu.run and nu.arun on the local backends, which hold open blobs;
s3 refuses them through the terms as its backend does.
"""

from __future__ import annotations

import asyncio
import threading
import time

import pytest
from _support.blob_workers import BUCKET, LOCAL_KINDS

import nu
import nustd
from nu.engine.validation import ValidationError
from nu.forms import Dict
from nustd.blob import (
    BlobAppend,
    BlobAppendStream,
    BlobIdle,
    BlobIsSealed,
    BlobNotFound,
    BlobSeal,
    BlobSealed,
    FilesBackend,
    LMDBBackend,
    StoreRef,
)


DATA = bytes(range(256)) * 40
PIECES = [DATA[i : i + 1000] for i in range(0, len(DATA), 1000)]
BID = "0123456789abcdef0123456789abcdef"

Media = StoreRef("media")
Pics = StoreRef("pics")


@pytest.fixture(params=LOCAL_KINDS)
def local(request):
    return request.param


@pytest.fixture(params=["sync", "async"])
def mode(request):
    return request.param


@pytest.fixture
def run(mode):
    def go(term):
        if mode == "sync":
            return nu.run(term)[0]
        return asyncio.run(nu.arun(term))[0]

    return go


def bind(kind, store, path):
    if kind == "s3":
        return nustd.blob.s3(store, bucket=BUCKET, prefix=f"{path.name}/")
    preset = nustd.blob.lmdb if kind == "lmdb" else nustd.blob.files
    return preset(store, path)


@pytest.fixture
def path(tmp_path):
    return tmp_path / "media"


@pytest.fixture
def media(local, path):
    return lambda body: nu.With(bind(local, Media, path), body=body)


@pytest.fixture
def backend(local, path):
    """A plain backend on the same store, for a writer beside the run."""
    made = LMDBBackend(path) if local == "lmdb" else FilesBackend(path)
    made.open()
    yield made
    made.close()


# --- the surface ------------------------------------------------------------------


def test_methods_build_the_matching_atoms():
    assert isinstance(Media.append(BID, b"x"), BlobAppend)
    assert isinstance(Media.append_stream(BID, Media.open(BID)), BlobAppendStream)
    assert isinstance(Media.seal(BID), BlobSeal)
    sealed = Media.sealed(BID)
    assert isinstance(sealed, nu.Bool)
    assert isinstance(nu.tree.children(sealed)[0], BlobIsSealed)


def test_kinds():
    assert isinstance(Media.append(BID, b"x"), nu.Command)
    assert isinstance(Media.append_stream(BID, Media.open(BID)), nu.CommandReduction)
    assert isinstance(Media.seal(BID), nu.Command)
    assert isinstance(nu.tree.children(Media.sealed(BID))[0], nu.ScalarQuery)


@pytest.mark.parametrize(
    "build",
    [
        lambda: Media.append("short", b"x"),
        lambda: Media.append_stream("short", nu.Iter([b"x"])),
        lambda: Media.seal("short"),
        lambda: Media.sealed("short"),
    ],
)
def test_malformed_str_id_is_refused_at_build(build):
    with pytest.raises(ValueError, match="32 lowercase hex"):
        build()


def test_follow_and_idle_are_keyword_only():
    with pytest.raises(TypeError):
        Media.open(BID, 0, None, 10, True)  # type: ignore[misc]


def test_new_errors_are_exported():
    assert nustd.blob.BlobSealed is BlobSealed
    assert nustd.blob.BlobIdle is BlobIdle


# --- runs ---------------------------------------------------------------------------


def test_put_unsealed_append_seal(media, run):
    bid = run(media(Media.put(DATA[:4000], seal=False)))
    assert run(media(Media.sealed(bid))) is False
    meta = run(media(Media.meta(bid)))
    assert (meta["size"], meta["sealed"]) == (4000, False)
    assert run(media(Media.append(bid, DATA[4000:7000]))) is None
    assert run(media(Media.append_stream(bid, nu.Iter(PIECES[7:])))) is None
    assert run(media(Media.seal(bid))) is None
    assert run(media(Media.sealed(bid))) is True
    assert run(media(Media.seal(bid))) is None  # sealing again is a no-op
    assert run(media(Media.get(bid))) == DATA


def test_put_stream_unsealed(media, run):
    bid = run(media(Media.put_stream(nu.Iter(PIECES[:3]), seal=False)))
    assert run(media(Media.meta(bid)))["sealed"] is False


def test_plain_put_is_sealed(media, run):
    bid = run(media(Media.put(b"x")))
    assert run(media(Media.sealed(bid))) is True


def test_one_program_appends_then_seals(media, run):
    bid = run(media(Media.put(b"ab", seal=False)))
    run(media(Media.append(bid, b"cd") >> Media.append(bid, b"ef") >> Media.seal(bid)))
    assert run(media(Dict.of(bytes=Media.get(bid), sealed=Media.sealed(bid)))) == {
        "bytes": b"abcdef",
        "sealed": True,
    }


def test_append_to_a_sealed_blob_raises(media, run):
    bid = run(media(Media.put(b"x")))
    with pytest.raises(BlobSealed):
        run(media(Media.append(bid, b"y")))


def test_seal_and_sealed_of_a_missing_blob_raise(media, run):
    with pytest.raises(BlobNotFound):
        run(media(Media.seal("f" * 32)))
    with pytest.raises(BlobNotFound):
        run(media(Media.sealed("f" * 32)))


def test_append_stream_of_a_scalar_is_refused(media, run):
    with pytest.raises(ValidationError, match="BlobAppendStream folds the stream in slot 2"):
        run(media(Media.append_stream(BID, nu.Literal(b"x"))))


def test_append_of_a_stream_term_is_refused(media, run):
    with pytest.raises(ValidationError, match="BlobAppend is fed a stream in slot 2"):
        run(media(Media.append(BID, Media.open(BID))))


def test_append_stream_copies_one_blob_onto_another(media, run):
    src = run(media(Media.put(DATA)))
    dst = run(media(Media.put(b"head:", seal=False)))
    run(media(Media.append_stream(dst, Media.open(src, step=999))))
    run(media(Media.seal(dst)))
    assert run(media(Media.get(dst))) == b"head:" + DATA


def test_open_follows_a_writer_until_sealed(media, run, backend):
    bid = backend.put(DATA[:1000], seal=False).id

    def write():
        for offset in range(1000, len(DATA), 2000):
            time.sleep(0.03)
            backend.append(bid, DATA[offset : offset + 2000])
        backend.seal(bid)

    writer = threading.Thread(target=write)
    writer.start()
    try:
        pieces = run(media(nu.Collect(Media.open(bid, step=500, follow=True))))
    finally:
        writer.join(10)
    assert b"".join(pieces) == DATA


def test_open_without_follow_reads_what_is_there(media, run, backend):
    bid = backend.put(DATA[:3000], seal=False).id
    assert b"".join(run(media(nu.Collect(Media.open(bid))))) == DATA[:3000]


def test_open_follow_idle_raises(media, run, backend):
    bid = backend.put(b"x", seal=False).id
    with pytest.raises(BlobIdle):
        run(media(nu.Collect(Media.open(bid, follow=True, idle=0.1))))


def test_follow_and_idle_may_be_terms(media, run, backend):
    bid = backend.put(b"x", seal=False).id
    with pytest.raises(BlobIdle):
        run(media(nu.Collect(Media.open(bid, follow=nu.Not(False), idle=nu.Add(0.05, 0.05)))))


def test_get_of_an_open_blob_waits_for_the_seal(media, run, backend):
    bid = backend.put(b"ab", seal=False).id

    def finish():
        time.sleep(0.2)
        backend.append(bid, b"cd")
        backend.seal(bid)

    writer = threading.Thread(target=finish)
    writer.start()
    try:
        assert run(media(Media.get(bid))) == b"abcd"
    finally:
        writer.join(10)


# --- s3 --------------------------------------------------------------------------------


@pytest.fixture
def s3_media(moto_s3, tmp_path):
    return lambda body: nu.With(bind("s3", Media, tmp_path / "media"), body=body)


def test_s3_refuses_open_blobs_through_the_terms(s3_media, run):
    with pytest.raises(NotImplementedError, match="no open blobs"):
        run(s3_media(Media.put(b"x", seal=False)))
    bid = run(s3_media(Media.put(b"x")))
    with pytest.raises(NotImplementedError, match="no open blobs"):
        run(s3_media(Media.append(bid, b"y")))
    assert run(s3_media(Media.sealed(bid))) is True
    run(s3_media(Media.seal(bid)))
    assert b"".join(run(s3_media(nu.Collect(Media.open(bid, follow=True))))) == b"x"
