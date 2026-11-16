"""What only the files backend promises: its layout, copy-not-link, meta as the visibility mark."""

from __future__ import annotations

import pytest

from nustd.blob import BlobNotFound, FilesBackend
from nustd.blob._base import new_id


@pytest.fixture
def files(tmp_path):
    backend = FilesBackend(tmp_path / "root")
    backend.open()
    yield backend
    backend.close()


def test_layout(files):
    info = files.put(b"hello", mime="text/plain")
    shard = files.root / "blobs" / info.id[:2]
    assert sorted(p.name for p in shard.iterdir()) == [info.id, f"{info.id}.json"]
    assert (shard / info.id).read_bytes() == b"hello"
    assert list((files.root / "tmp").iterdir()) == []


def test_path_source_is_copied_not_linked(files, tmp_path):
    source = tmp_path / "src.bin"
    source.write_bytes(b"original")
    info = files.put(source)
    assert source.stat().st_nlink == 1
    source.write_bytes(b"changed!")
    assert files.read(info.id) == b"original"


def test_spooled_iterable_is_linked_not_copied(files):
    info = files.put(iter([b"a", b"b"]))
    data = files.root / "blobs" / info.id[:2] / info.id
    assert data.stat().st_nlink == 1  # the spool link was dropped, the data kept
    assert data.read_bytes() == b"ab"


def test_data_without_meta_is_invisible(files):
    # What a put that died between the link and the meta leaves behind.
    info = files.put(b"half")
    meta = files.root / "blobs" / info.id[:2] / f"{info.id}.json"
    meta.unlink()
    assert not files.exists(info.id)
    with pytest.raises(BlobNotFound):
        files.read(info.id)
    with pytest.raises(BlobNotFound):
        next(files.stream(info.id))
    assert files.delete(info.id) is False
    assert not (files.root / "blobs" / info.id[:2] / info.id).exists()
    assert files.put(b"again", blob_id=info.id).id == info.id


def test_meta_failure_rolls_back_the_data(files, monkeypatch):
    def broken(info):
        raise OSError("disk full")

    monkeypatch.setattr(files, "_write_meta", broken)
    bid = new_id()
    with pytest.raises(OSError, match="disk full"):
        files.put(b"data", blob_id=bid)
    assert not (files.root / "blobs" / bid[:2] / bid).exists()
    assert list((files.root / "tmp").iterdir()) == []


def test_open_stream_survives_delete(files):
    info = files.put(b"x" * 300)
    pieces = files.stream(info.id, step=100)
    assert next(pieces) == b"x" * 100
    files.delete(info.id)
    assert b"".join(pieces) == b"x" * 200


def test_reopen_sees_blobs(tmp_path):
    first = FilesBackend(tmp_path / "root")
    first.open()
    info = first.put(b"kept", name="k")
    first.close()
    second = FilesBackend(tmp_path / "root")
    second.open()
    assert second.info(info.id) == info
    assert second.read(info.id) == b"kept"
