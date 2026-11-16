"""Every blob term run under nu.run and nu.arun, on every backend.

``kind`` (lmdb, files, s3) comes from conftest; ``mode`` picks the runner.
Local stores sit under ``tmp_path``: local disk, never the NFS repo tree. An
s3 store is a key prefix named after the path, in the moto bucket.
"""

from __future__ import annotations

import asyncio
import io

import pytest
from _support.blob_workers import BUCKET

import nu
import nustd
from nu.forms import Dict
from nustd.blob import (
    BlobExists,
    BlobFabric,
    BlobNotFound,
    FilesBackend,
    LMDBBackend,
    S3Backend,
    StoreRef,
)
from nustd.blob._base import check_id


DATA = bytes(range(256)) * 40  # 10240 bytes, every offset distinct mod 256


Media = StoreRef("media")
Pics = StoreRef("pics")


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
def media(kind, tmp_path):
    """The Media binding: wrap a body in it."""
    path = tmp_path / "media"
    return lambda body: nu.With(bind(kind, Media, path), body=body)


# --- put / get / meta / has / delete ----------------------------------------


def test_put_yields_an_id_and_get_reads_it_back(media, run):
    bid = run(media(Media.put(DATA)))
    assert check_id(bid) == bid
    assert run(media(Media.get(bid))) == DATA


def test_put_then_get_in_one_program(media, run):
    term = nu.let(Media.put(DATA), lambda bid: Media.get(bid))
    assert run(media(term)) == DATA


def test_meta(media, run):
    term = nu.let(
        Media.put(DATA, mime="image/png", name="cat.png"),
        lambda bid: Dict.of(bid=bid, meta=Media.meta(bid)),
    )
    out = run(media(term))
    meta = out["meta"]
    assert meta["id"] == out["bid"]
    assert meta["size"] == len(DATA)
    assert meta["mime"] == "image/png"
    assert meta["name"] == "cat.png"
    assert meta["created_at"] > 0
    assert set(meta) == {"id", "size", "mime", "name", "created_at"}


def test_has(media, run):
    bid = run(media(Media.put(b"x")))
    assert run(media(Media.has(bid))) is True
    assert run(media(Media.has("f" * 32))) is False


def test_delete(media, run):
    bid = run(media(Media.put(b"x")))
    assert run(media(Media.delete(bid))) is None
    assert run(media(Media.has(bid))) is False
    # A second delete is a no-op.
    run(media(Media.delete(bid)))


def test_get_and_meta_of_a_missing_id_raise(media, run):
    with pytest.raises(BlobNotFound):
        run(media(Media.get("f" * 32)))
    with pytest.raises(BlobNotFound):
        run(media(Media.meta("f" * 32)))


# --- minting ------------------------------------------------------------------


def test_put_mints_at_run_time(media, run):
    term = media(Media.put(b"same tree"))
    first, second = run(term), run(term)
    assert first != second
    assert run(media(Media.has(first))) and run(media(Media.has(second)))


def test_rebuilding_the_tree_mints_again(media, run):
    ids = {run(media(Media.put(b"x"))) for _ in range(3)}
    assert len(ids) == 3


def test_new_id_is_fresh_per_run(media, run):
    term = media(Media.new_id())
    first, second = run(term), run(term)
    assert check_id(first) == first
    assert first != second
    # Minting reserves nothing.
    assert run(media(Media.has(first))) is False


def test_put_under_a_minted_id(media, run):
    term = nu.let(
        Media.new_id(),
        lambda bid: Dict.of(minted=bid, put=Media.put(b"x", blob_id=bid)),
    )
    out = run(media(term))
    assert out["put"] == out["minted"]
    assert run(media(Media.get(out["minted"]))) == b"x"


def test_put_under_a_taken_id_raises(media, run):
    bid = run(media(Media.put(b"first")))
    with pytest.raises(BlobExists):
        run(media(Media.put(b"second", blob_id=bid)))
    assert run(media(Media.get(bid))) == b"first"


# --- sources --------------------------------------------------------------------


def test_put_from_a_path(media, run, tmp_path):
    src = tmp_path / "src.bin"
    src.write_bytes(DATA)
    bid = run(media(Media.put(src)))
    assert run(media(Media.get(bid))) == DATA


def test_put_from_a_file(media, run):
    bid = run(media(Media.put(io.BytesIO(DATA))))
    assert run(media(Media.get(bid))) == DATA


def test_put_from_an_iterable(media, run):
    bid = run(media(Media.put(iter([DATA[:100], DATA[100:]]))))
    assert run(media(Media.get(bid))) == DATA


def test_put_from_an_async_iterable_under_arun(media):
    async def pieces():
        for i in range(0, len(DATA), 1000):
            await asyncio.sleep(0)
            yield DATA[i : i + 1000]

    bid = asyncio.run(nu.arun(media(Media.put(pieces()))))[0]
    assert nu.run(media(Media.get(bid)))[0] == DATA


def test_put_from_an_async_iterable_under_run_is_refused(media):
    async def pieces():
        yield b"x"

    source = pieces()
    with pytest.raises(TypeError, match="aput"):
        nu.run(media(Media.put(source)))
    asyncio.run(source.aclose())


def test_put_of_a_str_is_refused(media, run):
    with pytest.raises(TypeError, match="ambiguous"):
        run(media(Media.put("text or a path?")))


# --- open -----------------------------------------------------------------------


def test_open_whole(media, run):
    term = nu.let(Media.put(DATA), lambda bid: nu.Collect(Media.open(bid, step=4096)))
    pieces = run(media(term))
    assert [len(p) for p in pieces] == [4096, 4096, 2048]
    assert b"".join(pieces) == DATA


def test_open_range(media, run):
    term = nu.let(Media.put(DATA), lambda bid: nu.Collect(Media.open(bid, 1000, 3500, 1000)))
    pieces = run(media(term))
    assert [len(p) for p in pieces] == [1000, 1000, 500]
    assert b"".join(pieces) == DATA[1000:3500]


def test_open_range_clamps(media, run):
    term = nu.let(Media.put(DATA), lambda bid: nu.Collect(Media.open(bid, 10000, 99999)))
    assert b"".join(run(media(term))) == DATA[10000:]


def test_open_of_a_missing_id_raises(media, run):
    with pytest.raises(BlobNotFound):
        run(media(nu.Collect(Media.open("f" * 32))))


# --- arguments as terms ----------------------------------------------------------


def test_every_argument_may_be_a_term(media, run):
    term = nu.let(
        Media.put(
            nu.Literal(DATA),
            mime=nu.Add("image/", "png"),
            name=nu.Add("cat", ".png"),
        ),
        lambda bid: Dict.of(
            meta=Media.meta(bid),
            has=Media.has(bid),
            part=nu.Collect(Media.open(bid, nu.Add(10, 10), nu.Add(30, 10), nu.Add(5, 5))),
        ),
    )
    out = run(media(term))
    assert out["meta"]["mime"] == "image/png"
    assert out["meta"]["name"] == "cat.png"
    assert out["has"] is True
    assert out["part"] == [DATA[20:30], DATA[30:40]]


# --- two stores ------------------------------------------------------------------


def test_two_stores_in_one_tree_stay_apart(kind, tmp_path, run):
    other = "files" if kind == "lmdb" else "lmdb"
    tree = lambda body: nu.With(  # noqa: E731
        bind(kind, Media, tmp_path / "media"),
        bind(other, Pics, tmp_path / "pics"),
        body=body,
    )
    term = nu.let(
        Media.put(b"in media"),
        lambda a: nu.let(
            Pics.put(b"in pics"),
            lambda b: Dict.of(
                a=a,
                b=b,
                a_in_media=Media.has(a),
                a_in_pics=Pics.has(a),
                b_in_media=Media.has(b),
                b_in_pics=Pics.has(b),
            ),
        ),
    )
    out = run(tree(term))
    assert out["a_in_media"] and out["b_in_pics"]
    assert not out["a_in_pics"] and not out["b_in_media"]
    assert run(tree(Media.get(out["a"]))) == b"in media"
    with pytest.raises(BlobNotFound):
        run(tree(Pics.get(out["a"])))


def test_two_stores_of_one_kind_stay_apart(kind, tmp_path, run):
    tree = lambda body: nu.With(  # noqa: E731
        bind(kind, Media, tmp_path / "media"),
        bind(kind, Pics, tmp_path / "pics"),
        body=body,
    )
    a = run(tree(Media.put(b"a")))
    assert run(tree(Media.has(a))) is True
    assert run(tree(Pics.has(a))) is False


def test_unbound_store_raises_naming_it(kind, tmp_path, run):
    term = nu.With(bind(kind, Media, tmp_path / "media"), body=Pics.has("f" * 32))
    with pytest.raises(RuntimeError, match="no blob backend is bound for pics"):
        run(term)


def test_store_named_by_a_str_reaches_the_ref_binding(kind, tmp_path, run):
    """A preset given the name binds what the ``StoreRef`` of that name reads."""
    path = tmp_path / "media"
    bid = run(nu.With(bind(kind, "media", path), body=Media.put(b"by name")))
    assert run(nu.With(bind(kind, Media, path), body=Media.get(bid))) == b"by name"
    assert run(nu.With(bind(kind, "media", path), body=StoreRef("media").get(bid))) == b"by name"


def test_two_refs_of_one_name_are_one_store(kind, tmp_path, run):
    again = StoreRef("media")
    term = nu.With(
        bind(kind, Media, tmp_path / "media"),
        body=nu.let(Media.put(b"x"), lambda bid: again.get(bid)),
    )
    assert run(term) == b"x"


# --- lifecycle --------------------------------------------------------------------


class Spy:
    """Records open and close of the backends a test builds."""

    events: list[str] = []  # noqa: RUF012


class SpyFiles(FilesBackend):
    def open(self):
        Spy.events.append("open")
        super().open()

    def close(self):
        Spy.events.append("close")
        super().close()


class SpyLMDB(LMDBBackend):
    def open(self):
        Spy.events.append("open")
        super().open()

    def close(self):
        Spy.events.append("close")
        super().close()


class SpyS3(S3Backend):
    def open(self):
        Spy.events.append("open")
        super().open()

    def close(self):
        Spy.events.append("close")
        super().close()


def spy_bind(kind, path):
    if kind == "s3":
        spec = {"backend": SpyS3, "options": {"bucket": BUCKET, "prefix": f"{path.name}/"}}
    elif kind == "lmdb":
        spec = {"backend": SpyLMDB, "options": {"path": str(path)}}
    else:
        spec = {"backend": SpyFiles, "options": {"root": str(path)}}
    return nu.Provide(BlobFabric, spec, tag=Media.name)


def test_backend_opens_on_enter_and_closes_on_exit(kind, tmp_path, run):
    Spy.events.clear()
    term = nu.With(spy_bind(kind, tmp_path / "s"), body=Media.put(b"x"))
    bid = run(term)
    assert Spy.events == ["open", "close"]
    assert check_id(bid) == bid


def test_backend_closes_when_the_body_raises(kind, tmp_path, run):
    Spy.events.clear()
    term = nu.With(spy_bind(kind, tmp_path / "s"), body=Media.get("f" * 32))
    with pytest.raises(BlobNotFound):
        run(term)
    assert Spy.events == ["open", "close"]


def test_each_run_opens_its_own_backend(kind, tmp_path, run):
    Spy.events.clear()
    term = nu.With(spy_bind(kind, tmp_path / "s"), body=Media.put(b"x"))
    run(term)
    run(term)
    assert Spy.events == ["open", "close", "open", "close"]


def test_fabric_refuses_use_outside_its_bracket(tmp_path):
    fabric = BlobFabric(backend=FilesBackend, options={"root": str(tmp_path)})
    with pytest.raises(RuntimeError, match="not open"):
        fabric.backend  # noqa: B018
    fabric.setup(None)
    assert fabric.backend.put(b"x").size == 1
    fabric.cleanup()
    with pytest.raises(RuntimeError, match="not open"):
        fabric.backend  # noqa: B018


# --- ref -------------------------------------------------------------------------


def test_store_exists_sees_its_own_binding_only(kind, tmp_path, run):
    term = nu.With(
        bind(kind, Media, tmp_path / "media"),
        body=Dict.of(media=Media.exists(), pics=Pics.exists()),
    )
    assert run(term) == {"media": True, "pics": False}
    assert run(Media.exists()) is False


def test_store_read_is_the_bound_fabric(kind, tmp_path, run):
    term = nu.With(bind(kind, Media, tmp_path / "media"), body=Media)
    assert isinstance(run(term), BlobFabric)
