"""The StoreRef surface: names, build-time checks, presets and specs, no run needed."""

from __future__ import annotations

import pytest

import nu
import nustd
from nu.lang.null import is_null
from nustd.blob import (
    BlobDelete,
    BlobFabric,
    BlobGet,
    BlobHas,
    BlobMeta,
    BlobNewId,
    BlobOpen,
    BlobPut,
    BlobPutStream,
    FilesBackend,
    LMDBBackend,
    S3Backend,
    StoreRef,
    backend_of,
)
from nustd.blob.store import store_name


BID = "0123456789abcdef0123456789abcdef"

Media = StoreRef("media")
Pics = StoreRef("pics-v1")


def test_registered_as_a_lazy_fabric():
    assert "blob" in dir(nustd)
    assert nustd.blob.StoreRef is StoreRef
    assert nustd.blob.backend_of is backend_of


def test_old_surface_is_gone():
    for gone in ("Store", "URL_PREFIX", "routes"):
        assert not hasattr(nustd.blob, gone)
        assert gone not in nustd.blob.__all__


def test_is_a_fabric_ref_over_the_blob_fabric():
    assert isinstance(Media, nu.context.FabricRef)
    assert StoreRef.fabric is BlobFabric


def test_name():
    assert Media.name == "media"
    assert Pics.name == "pics-v1"


@pytest.mark.parametrize("name", ["Media", "a b", ".hidden", "a/b", "кот"])
def test_any_non_empty_str_is_a_name(name):
    assert StoreRef(name).name == name


@pytest.mark.parametrize("bad", ["", None, 42, b"media", StoreRef])
def test_name_that_is_no_non_empty_str_is_refused(bad):
    with pytest.raises(TypeError, match="non-empty str"):
        StoreRef(bad)


def test_store_name_takes_a_ref_or_its_name():
    assert store_name(Media) == "media"
    assert store_name("pics") == "pics"
    with pytest.raises(TypeError, match="non-empty str"):
        store_name("")
    with pytest.raises(TypeError, match="non-empty str"):
        store_name(object())


def test_store_knows_no_urls():
    assert not hasattr(Media, "url")
    assert not hasattr(Media, "upload_url")


def test_methods_build_the_matching_atoms():
    assert isinstance(Media.put(b"x"), BlobPut)
    assert isinstance(Media.put_stream(Media.open(BID)), BlobPutStream)
    assert isinstance(Media.new_id(), BlobNewId)
    assert isinstance(Media.get(BID), BlobGet)
    assert isinstance(Media.open(BID), BlobOpen)
    assert isinstance(Media.meta(BID), BlobMeta)
    assert isinstance(Media.has(BID), BlobHas)
    assert isinstance(Media.delete(BID), BlobDelete)


def test_exists_asks_whether_a_backend_is_bound():
    term = Media.exists()
    assert isinstance(term, nu.Bool)
    assert not isinstance(term, BlobHas)


def test_each_term_holds_the_ref_it_was_built_from():
    first, second = Media.get(BID), Media.has(BID)
    assert first._children[0] is Media
    assert second._children[0] is Media


def test_atoms_take_a_store_ref_directly():
    term = BlobGet(StoreRef("media"), BID)
    assert isinstance(term._children[0], StoreRef)
    assert term._children[0].name == "media"


@pytest.mark.parametrize("store", [StoreRef, "media", None], ids=["class", "name", "none"])
@pytest.mark.parametrize(
    "build",
    [
        lambda store: BlobGet(store, BID),
        lambda store: BlobPut(store, b"x", None, "", ""),
        lambda store: BlobPutStream(store, nu.Iter([b"x"]), None, "", ""),
        lambda store: BlobNewId(store),
        lambda store: BlobOpen(store, BID, 0, None, 1024),
        lambda store: BlobMeta(store, BID),
        lambda store: BlobHas(store, BID),
        lambda store: BlobDelete(store, BID),
    ],
    ids=["get", "put", "put_stream", "new_id", "open", "meta", "has", "delete"],
)
def test_store_slot_that_is_no_term_is_refused(build, store):
    with pytest.raises(TypeError, match="the store slot is a term"):
        build(store)


@pytest.mark.parametrize(
    "build",
    [
        lambda: Media.get("nope"),
        lambda: Media.open("NOPE"),
        lambda: Media.meta("x" * 32),
        lambda: Media.has(""),
        lambda: Media.delete("../x"),
        lambda: Media.put(b"x", blob_id="short"),
        lambda: Media.put_stream(nu.Iter([b"x"]), blob_id="short"),
    ],
)
def test_malformed_str_id_is_refused_at_build(build):
    with pytest.raises(ValueError, match="32 lowercase hex"):
        build()


def test_build_mints_nothing():
    # The id is minted when the put runs; the tree holds no id at all.
    term = Media.put(b"x")
    assert term._children[2]._payload["value"] is None


def test_kinds():
    assert isinstance(Media.put(b"x"), nu.ScalarAction)
    assert isinstance(Media.put_stream(Media.open(BID)), nu.ActionReduction)
    assert isinstance(Media.put_stream(Media.open(BID)), nu.ScalarAction)
    assert isinstance(Media.new_id(), nu.ScalarQuery)
    assert isinstance(Media.open(BID), nu.StreamQuery)
    assert isinstance(Media.delete(BID), nu.Command)


def test_unbound_store_reads_null_and_does_not_exist():
    assert nu.run(Media.exists())[0] is False
    assert is_null(nu.run(Media)[0])


# --- presets and specs -----------------------------------------------------------


@pytest.mark.parametrize("store", [Media, "media"], ids=["ref", "name"])
def test_preset_binds_under_the_store_name(store, tmp_path):
    for spec in (
        nustd.blob.lmdb(store, tmp_path / "env"),
        nustd.blob.files(store, tmp_path / "files"),
        nustd.blob.s3(store, bucket="b"),
    ):
        assert spec._payload["cls"] is BlobFabric
        assert spec._payload["tags"] == ("media",)


def test_a_str_name_reaches_the_same_store(tmp_path):
    """``lmdb("media", path)`` binds what ``StoreRef("media")`` reads."""
    term = nu.With(nustd.blob.lmdb("media", tmp_path / "env"), body=Media.exists())
    assert nu.run(term)[0] is True
    other = nu.With(nustd.blob.lmdb("pics", tmp_path / "env"), body=Media.exists())
    assert nu.run(other)[0] is False


@pytest.mark.parametrize("bad", ["", None, StoreRef])
def test_preset_refuses_what_is_no_store(bad, tmp_path):
    with pytest.raises(TypeError, match="non-empty str"):
        nustd.blob.lmdb(bad, tmp_path)
    with pytest.raises(TypeError, match="non-empty str"):
        nustd.blob.files(bad, tmp_path)
    with pytest.raises(TypeError, match="non-empty str"):
        nustd.blob.s3(bad, bucket="b")


def test_backend_of_lmdb(tmp_path):
    spec = nustd.blob.lmdb(
        Media, tmp_path / "env", map_size=1 << 24, max_readers=16, writemap=False
    )
    backend = backend_of(spec)
    assert type(backend) is LMDBBackend
    assert backend._env is None
    assert backend.map_size == 1 << 24
    assert backend.max_readers == 16
    assert backend.writemap is False
    assert not (tmp_path / "env").exists()  # not opened


def test_backend_of_files(tmp_path):
    backend = backend_of(nustd.blob.files(Media, tmp_path / "files"))
    assert type(backend) is FilesBackend
    assert backend.root == tmp_path / "files"
    assert not (tmp_path / "files").exists()  # not opened


def test_backend_of_s3():
    spec = nustd.blob.s3(Media, bucket="media", prefix="space/", endpoint_url="http://s3.test")
    backend = backend_of(spec)
    assert type(backend) is S3Backend
    assert backend.bucket == "media"
    assert backend.prefix == "space/"
    assert backend.endpoint_url == "http://s3.test"
    assert backend._client is None  # not opened


def test_backend_of_builds_a_new_backend_each_call(tmp_path):
    spec = nustd.blob.files(Media, tmp_path)
    assert backend_of(spec) is not backend_of(spec)


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "media",
        Media,
        {"backend": FilesBackend, "options": {}},
        nu.Provide(dict, {}, tag="media"),
    ],
    ids=["none", "str", "ref", "dict", "other-provide"],
)
def test_backend_of_refuses_what_is_no_spec(bad):
    with pytest.raises(TypeError, match="a blob spec"):
        backend_of(bad)
