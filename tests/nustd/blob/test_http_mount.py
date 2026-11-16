"""BlobMount: where a server serves one blob store, and the urls that reach it, no server needed."""

from __future__ import annotations

import pytest

import nu
import nustd.blob
from nustd.blob.http import BlobMount


BID = "0123456789abcdef0123456789abcdef"


def test_exported_from_blob_http():
    assert nustd.blob.http.BlobMount is BlobMount
    assert "BlobMount" in nustd.blob.http.__all__


@pytest.mark.parametrize("at", ["/files", "/files/media", "/a.b~c_d-e/x1"])
def test_at_is_a_path(at):
    mount = BlobMount(at)
    assert mount.at == at
    assert mount.max_upload is None
    assert mount.cross_site is False


@pytest.mark.parametrize(
    "at",
    ["", "/", "files", "/files/", "//files", "/a b", "/files?x=1", "/fíles", "/files//media", 42],
)
def test_at_that_is_no_path_is_refused(at):
    with pytest.raises(ValueError, match="a mount is a path"):
        BlobMount(at)


def test_upload_rules():
    mount = BlobMount("/files", max_upload=1 << 20, cross_site=True)
    assert mount.max_upload == 1 << 20
    assert mount.cross_site is True
    assert BlobMount("/files", max_upload=0).max_upload == 0


@pytest.mark.parametrize("at", ["/.", "/a/..", "/../x"])
def test_dot_segments_are_refused(at):
    with pytest.raises(ValueError, match="a mount is a path"):
        BlobMount(at)


@pytest.mark.parametrize("cap", ["10", 1.5, True])
def test_a_cap_that_is_no_byte_count_is_refused(cap):
    with pytest.raises(ValueError, match="max_upload is a byte count"):
        BlobMount("/x", max_upload=cap)


def test_negative_max_upload_is_refused():
    with pytest.raises(ValueError, match="max_upload is a byte count"):
        BlobMount("/files", max_upload=-1)


def test_url_of_a_str_id_is_a_str():
    assert BlobMount("/files").url(BID) == f"/files/{BID}"
    assert BlobMount("/files/media").url(BID) == f"/files/media/{BID}"


def test_url_for_download():
    assert BlobMount("/files").url(BID, download=True) == f"/files/{BID}?download=1"


@pytest.mark.parametrize("bad", ["../../etc/passwd", "nope", "A" * 32, "a" * 33, ""])
def test_url_of_a_malformed_str_id_is_refused(bad):
    with pytest.raises(ValueError, match="32 lowercase hex"):
        BlobMount("/files").url(bad)


def test_url_of_a_term_id_is_a_term():
    files = BlobMount("/files")
    term = files.url(nu.Literal(BID))
    assert isinstance(term, nu.Nu)
    assert nu.run(term)[0] == f"/files/{BID}"
    download = files.url(nu.Literal(BID), download=True)
    assert nu.run(download)[0] == f"/files/{BID}?download=1"


def test_upload_url_is_the_mount():
    assert BlobMount("/files").upload_url() == "/files"
    assert BlobMount("/files/media").upload_url() == "/files/media"


def test_repr():
    assert repr(BlobMount("/files")) == "BlobMount('/files')"
