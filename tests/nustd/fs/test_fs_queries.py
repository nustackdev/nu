"""The query atoms on a real mount, each under nu.run and nu.arun."""

from __future__ import annotations

import hashlib
import threading
from pathlib import PurePath, PurePosixPath

import pytest

import nu
import nustd.fs.fabric as fabric_mod
from nustd import fs
from nustd.pathlib import Path


data = fs.FsRef("data")


def on(root, body, **kwargs):
    """``body`` run with ``root`` mounted under the ``data`` tag."""
    return fs.mount(root, tag="data", body=body, **kwargs)


# --- read_text / read_bytes -------------------------------------------------


def test_read_text(go, root):
    assert go(on(root, data.read_text("a.txt"))) == "hello\nworld\n"


def test_read_text_takes_a_pure_path_and_a_path_term(go, root):
    assert go(on(root, data.read_text(PurePath("docs/notes.md")))) == "notes"
    assert go(on(root, data.read_text(Path.of("docs", "notes.md")))) == "notes"


def test_read_text_missing_raises_without_default(go, root):
    with pytest.raises(FileNotFoundError):
        go(on(root, data.read_text("nope.txt")))


def test_read_text_default_on_missing(go, root):
    assert go(on(root, data.read_text("nope.txt", default=""))) == ""
    assert go(on(root, data.read_text("nope.txt", default=None))) is None


def test_read_text_default_does_not_cover_a_dir(go, root):
    with pytest.raises(IsADirectoryError):
        go(on(root, data.read_text("docs", default="")))


def test_read_text_encoding(go, root):
    (root / "l1.txt").write_bytes("caf\xe9".encode("latin-1"))
    assert go(on(root, data.read_text("l1.txt", encoding="latin-1"))) == "caf\xe9"
    with pytest.raises(UnicodeDecodeError):
        go(on(root, data.read_text("l1.txt")))


def test_read_bytes_whole_and_ranges(go, root):
    full = bytes(range(256))
    assert go(on(root, data.read_bytes("bin.dat"))) == full
    assert go(on(root, data.read_bytes("bin.dat", 10, 20))) == full[10:20]
    assert go(on(root, data.read_bytes("bin.dat", 250, 999))) == full[250:]
    assert go(on(root, data.read_bytes("bin.dat", 999))) == b""
    assert go(on(root, data.read_bytes("bin.dat", 20, 10))) == b""


def test_read_bytes_refuses_a_negative_bound(go, root):
    with pytest.raises(ValueError, match="negative"):
        go(on(root, data.read_bytes("bin.dat", -1)))


def test_read_bytes_default(go, root):
    assert go(on(root, data.read_bytes("nope", default=b"x"))) == b"x"


# --- stat / has / usage / where / digest ------------------------------------


def test_stat_gives_the_entry(go, root):
    row = go(on(root, data.stat("docs/notes.md")))
    assert row["path"] == PurePosixPath("docs/notes.md")
    assert row["name"] == "notes.md"
    assert row["kind"] == "file"
    assert row["size"] == 5
    assert row["mtime"] == pytest.approx((root / "docs" / "notes.md").stat().st_mtime)
    assert row["mode"] == (root / "docs" / "notes.md").stat().st_mode & 0o7777


def test_stat_of_a_dir_and_the_mount(go, root):
    assert go(on(root, data.stat("docs")))["kind"] == "dir"
    assert go(on(root, data.stat(".")))["path"] == PurePosixPath(".")


def test_stat_missing_is_none(go, root):
    assert go(on(root, data.stat("nope"))) is None
    assert go(on(root, data.stat("a.txt/under"))) is None


def test_has(go, root):
    assert go(on(root, data.has("a.txt"))) is True
    assert go(on(root, data.has("docs"))) is True
    assert go(on(root, data.has("nope"))) is False
    assert go(on(root, data.has("a.txt", kind="file"))) is True
    assert go(on(root, data.has("a.txt", kind="dir"))) is False
    assert go(on(root, data.has("docs", kind="dir"))) is True
    assert go(on(root, data.has("docs", kind="file"))) is False


def test_has_refuses_an_unknown_kind(go, root):
    with pytest.raises(ValueError, match="kind"):
        go(on(root, data.has("a.txt", kind="link")))


def test_usage(go, root):
    got = go(on(root, data.usage()))
    assert set(got) == {"total", "free", "used"}
    assert got["total"] > 0
    assert 0 <= got["free"] <= got["total"]


def test_where(go, root):
    real = root.resolve()
    assert go(on(root, data.where())) == str(real)
    assert go(on(root, data.where("docs/x"))) == str(real / "docs" / "x")


def test_digest(go, root):
    want = hashlib.sha256(bytes(range(256))).hexdigest()
    assert go(on(root, data.digest("bin.dat"))) == want
    md5 = hashlib.md5(bytes(range(256))).hexdigest()  # noqa: S324 - a test of the algo slot
    assert go(on(root, data.digest("bin.dat", algo="md5"))) == md5


def test_digest_of_a_big_file_spans_pieces(go, root, monkeypatch):
    monkeypatch.setattr(fabric_mod, "STEP", 7)
    blob = bytes(range(256)) * 9
    (root / "big").write_bytes(blob)
    assert go(on(root, data.digest("big"))) == hashlib.sha256(blob).hexdigest()


# --- list -------------------------------------------------------------------


def _paths(rows):
    return [str(r["path"]) for r in rows]


def test_list_top(go, root):
    rows = go(on(root, nu.Collect(data.list())))
    assert _paths(rows) == ["a.txt", "bin.dat", "docs", "empty"]
    assert {r["kind"] for r in rows} == {"file", "dir"}


def test_list_a_subdir(go, root):
    rows = go(on(root, nu.Collect(data.list("docs"))))
    assert _paths(rows) == ["docs/notes.md", "docs/readme.md", "docs/sub"]


def test_list_recursive(go, root):
    rows = go(on(root, nu.Collect(data.list("docs", recursive=True))))
    assert _paths(rows) == ["docs/notes.md", "docs/readme.md", "docs/sub", "docs/sub/deep.md"]


def test_list_pattern_and_kind(go, root):
    md = go(on(root, nu.Collect(data.list(".", pattern="*.md", recursive=True))))
    assert _paths(md) == ["docs/notes.md", "docs/readme.md", "docs/sub/deep.md"]
    dirs = go(on(root, nu.Collect(data.list(".", recursive=True, kind="dir"))))
    assert _paths(dirs) == ["docs", "docs/sub", "empty"]


def test_list_shows_links_and_never_walks_them(go, root):
    (root / "ln").symlink_to(root / "docs")
    rows = go(on(root, nu.Collect(data.list(".", recursive=True, kind="link"))))
    assert _paths(rows) == ["ln"]
    every = _paths(go(on(root, nu.Collect(data.list(".", recursive=True)))))
    assert not any(p.startswith("ln/") for p in every)


def test_list_empty_dir(go, root):
    assert go(on(root, nu.Collect(data.list("empty")))) == []


def test_list_missing_and_file(go, root):
    with pytest.raises(FileNotFoundError):
        go(on(root, nu.Collect(data.list("nope"))))
    with pytest.raises(NotADirectoryError):
        go(on(root, nu.Collect(data.list("a.txt"))))


def test_list_refuses_an_unknown_kind(go, root):
    with pytest.raises(ValueError, match="kind"):
        go(on(root, nu.Collect(data.list(kind="pipe"))))


# --- open / lines -----------------------------------------------------------


def test_open_pieces(go, root):
    full = bytes(range(256))
    pieces = go(on(root, nu.Collect(data.open("bin.dat", step=100))))
    assert [len(p) for p in pieces] == [100, 100, 56]
    assert b"".join(pieces) == full


def test_open_ranges(go, root):
    full = bytes(range(256))
    got = go(on(root, nu.Collect(data.open("bin.dat", 10, 35, step=10))))
    assert got == [full[10:20], full[20:30], full[30:35]]
    assert go(on(root, nu.Collect(data.open("bin.dat", 300)))) == []
    assert b"".join(go(on(root, nu.Collect(data.open("bin.dat", 200, 999))))) == full[200:]


def test_open_refuses_bad_step(go, root):
    with pytest.raises(ValueError, match="step"):
        go(on(root, nu.Collect(data.open("bin.dat", step=0))))


def test_open_missing(go, root):
    with pytest.raises(FileNotFoundError):
        go(on(root, nu.Collect(data.open("nope"))))


def test_open_is_lazy_and_async_reads_off_the_loop(go, root, monkeypatch):
    reads: list[int] = []
    real = fabric_mod._pieces

    def counted(*args):
        for piece in real(*args):
            reads.append(threading.get_ident())
            yield piece

    monkeypatch.setattr(fabric_mod, "_pieces", counted)
    first = go(on(root, nu.First(data.open("bin.dat", step=10))))
    assert first == bytes(range(10))
    assert len(reads) == 1
    if go.mode == "async":
        assert reads[0] != threading.get_ident()


def test_lines(go, root):
    assert go(on(root, nu.Collect(data.lines("a.txt")))) == ["hello", "world"]


def test_lines_crlf_and_no_last_newline(go, root):
    (root / "crlf.txt").write_bytes(b"one\r\ntwo\r\nthree")
    assert go(on(root, nu.Collect(data.lines("crlf.txt")))) == ["one", "two", "three"]


def test_lines_keep_chaining(go, root):
    upper = data.lines("a.txt").map(lambda line: nu.Str(line).upper())
    assert go(on(root, upper.to_list())) == ["HELLO", "WORLD"]
    assert go(on(root, (data / "docs" / "notes.md").lines().count())) == 1


def test_lines_of_an_empty_file(go, root):
    (root / "empty.txt").write_text("")
    assert go(on(root, nu.Collect(data.lines("empty.txt")))) == []


# --- FileRef ----------------------------------------------------------------


def test_file_ref_builds_the_same_verbs(go, root):
    notes = data / "docs" / "notes.md"
    assert go(on(root, notes.read_text())) == "notes"
    assert go(on(root, notes.read_bytes(0, 3))) == b"not"
    assert go(on(root, notes.stat()))["name"] == "notes.md"
    assert go(on(root, notes.exists())) is True
    assert go(on(root, notes.has(kind="dir"))) is False
    assert go(on(root, notes.where())) == str(root.resolve() / "docs" / "notes.md")
    assert go(on(root, notes.digest())) == hashlib.sha256(b"notes").hexdigest()
    assert go(on(root, nu.Collect(notes.lines()))) == ["notes"]
    assert go(on(root, nu.Collect(notes.open(step=2)))) == [b"no", b"te", b"s"]
    docs = data.file("docs")
    assert _paths(go(on(root, nu.Collect(docs.list(pattern="r*"))))) == ["docs/readme.md"]


def test_file_ref_missing(go, root):
    assert go(on(root, (data / "nope").exists())) is False
    assert go(on(root, (data / "nope").read_text(default="-"))) == "-"


def test_file_ref_joins_a_term_part_at_run_time(go, root):
    name = nu.Literal("notes.md")
    notes = data / "docs" / name
    assert go(on(root, notes.read_text())) == "notes"


def test_file_ref_path_form(go, root):
    notes = data / "docs" / "notes.md"
    assert notes.p == PurePosixPath("docs/notes.md")
    assert go(on(root, notes.path.name())) == "notes.md"
    assert go(on(root, notes.path.suffix())) == ".md"


def test_file_ref_is_immutable():
    f = data / "a"
    with pytest.raises(AttributeError, match="immutable"):
        f._path = "b"  # type: ignore[misc]
    assert f.fs is data


def test_file_ref_refuses_a_non_ref_and_a_bad_path():
    with pytest.raises(TypeError, match="FsRef"):
        fs.FileRef("data", "a")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="fs path"):
        data / 3  # type: ignore[operator]


def test_term_needs_a_term_in_the_mount_slot():
    with pytest.raises(TypeError, match="mount slot"):
        fs.FsReadText("data", "a.txt")
