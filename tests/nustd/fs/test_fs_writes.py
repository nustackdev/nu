"""The write atoms on a real mount, each under nu.run and nu.arun."""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import PurePosixPath

import pytest

import nu
import nustd.fs.fabric as fabric_mod
from nustd import fs


data = fs.FsRef("data")


def on(root, body, **kwargs):
    """``body`` run with ``root`` mounted under the ``data`` tag."""
    return fs.mount(root, tag="data", body=body, **kwargs)


def names(folder):
    """Every name under ``folder``, relative, sorted: a listing to spot strays in."""
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*"))


def strays(folder):
    """The temp and part files a write left behind."""
    return [n for n in names(folder) if n.endswith((".tmp", ".part"))]


# --- write_text / write_bytes -----------------------------------------------


def test_write_text_makes_parents(go, root):
    go(on(root, data.write_text("new/deep/n.txt", "hi")))
    assert (root / "new" / "deep" / "n.txt").read_text() == "hi"


def test_write_text_replaces_whole_and_leaves_no_temp(go, root):
    go(on(root, data.write_text("a.txt", "short")))
    assert (root / "a.txt").read_text() == "short"
    assert strays(root) == []


def test_write_text_is_idempotent(go, root):
    term = data.write_text("x.txt", "once")
    go(on(root, nu.Sequential(term, term)))
    assert (root / "x.txt").read_text() == "once"


def test_write_text_refuses_bytes(go, root):
    with pytest.raises(TypeError, match="write_bytes"):
        go(on(root, data.write_text("x.txt", b"raw")))


def test_write_bytes(go, root):
    go(on(root, data.write_bytes("b.bin", b"\x00\x01")))
    assert (root / "b.bin").read_bytes() == b"\x00\x01"


def test_write_bytes_refuses_text(go, root):
    with pytest.raises(TypeError, match="write_text"):
        go(on(root, data.write_bytes("b.bin", "text")))


def test_write_keeps_the_replaced_mode_or_sets_one(go, root):
    (root / "a.txt").chmod(0o600)
    go(on(root, data.write_text("a.txt", "new")))
    assert (root / "a.txt").stat().st_mode & 0o777 == 0o600
    go(on(root, data.write_text("m.txt", "new", mode=0o640)))
    assert (root / "m.txt").stat().st_mode & 0o777 == 0o640


def test_write_exclusive_refuses_a_taken_name(go, root):
    with pytest.raises(FileExistsError):
        go(on(root, data.write_text("a.txt", "clobber", exclusive=True)))
    assert (root / "a.txt").read_text() == "hello\nworld\n"
    assert strays(root) == []


def test_write_exclusive_takes_a_free_name(go, root):
    go(on(root, data.write_bytes("free.bin", b"x", exclusive=True)))
    assert (root / "free.bin").read_bytes() == b"x"
    assert strays(root) == []


def test_write_exclusive_loses_a_race_at_the_link(root, monkeypatch):
    # Taken between the check and the link: the link refuses, the temp goes.
    real_link = os.link

    def racing_link(src, dst, **kw):
        with open(dst, "w") as f:  # noqa: PTH123 - another writer lands first
            f.write("theirs")
        return real_link(src, dst, **kw)

    monkeypatch.setattr(os, "link", racing_link)
    with pytest.raises(FileExistsError):
        nu.run(on(root, data.write_text("race.txt", "mine", exclusive=True)))
    assert (root / "race.txt").read_text() == "theirs"
    assert strays(root) == []


def test_write_to_a_dir_raises(go, root):
    with pytest.raises(IsADirectoryError):
        go(on(root, data.write_text("docs", "x")))
    with pytest.raises(IsADirectoryError):
        go(on(root, data.write_text(".", "x")))


def test_failed_write_leaves_the_file_and_no_temp(go, root, monkeypatch):
    def broken(fd, full, mode):
        raise OSError("disk full")

    monkeypatch.setattr(fabric_mod, "_settle", broken)
    with pytest.raises(OSError, match="disk full"):
        go(on(root, data.write_text("a.txt", "new")))
    assert (root / "a.txt").read_text() == "hello\nworld\n"
    assert strays(root) == []


# --- write_stream -----------------------------------------------------------


def test_write_stream_folds_pieces(go, root):
    go(on(root, data.write_stream("s.bin", nu.Iter([b"ab", b"cd", "ef"]))))
    assert (root / "s.bin").read_bytes() == b"abcdef"
    assert strays(root) == []


def test_write_stream_from_another_file(go, root):
    go(on(root, data.write_stream("copy.dat", data.open("bin.dat", step=7))))
    assert (root / "copy.dat").read_bytes() == bytes(range(256))


def test_write_stream_of_nothing_makes_an_empty_file(go, root):
    go(on(root, data.write_stream("e.bin", nu.Iter([]))))
    assert (root / "e.bin").read_bytes() == b""


def test_write_stream_that_raises_leaves_no_part(go, root):
    (root / "s.bin").write_bytes(b"old")
    with pytest.raises(FileNotFoundError):
        go(on(root, data.write_stream("s.bin", data.open("missing.bin"))))
    assert (root / "s.bin").read_bytes() == b"old"
    assert strays(root) == []


def test_write_stream_exclusive(go, root):
    with pytest.raises(FileExistsError):
        go(on(root, data.write_stream("a.txt", nu.Iter([b"x"]), exclusive=True)))
    assert (root / "a.txt").read_text() == "hello\nworld\n"
    go(on(root, data.write_stream("free.bin", nu.Iter([b"x"]), exclusive=True)))
    assert (root / "free.bin").read_bytes() == b"x"
    assert strays(root) == []


# --- append / append_stream -------------------------------------------------


def test_append_adds_text_as_given(go, root):
    go(on(root, nu.Sequential(data.append("log/app.log", "a\n"), data.append("log/app.log", "b"))))
    assert (root / "log" / "app.log").read_text() == "a\nb"


def test_append_takes_bytes(go, root):
    go(on(root, data.append("a.txt", b"!")))
    assert (root / "a.txt").read_text() == "hello\nworld\n!"


def test_append_stream_adds_a_newline_per_line(go, root):
    go(on(root, data.append_stream("a.txt", nu.Iter(["x", "y"]))))
    assert (root / "a.txt").read_text() == "hello\nworld\nx\ny\n"


def test_append_stream_refuses_non_text(go, root):
    with pytest.raises(TypeError, match="str lines"):
        go(on(root, data.append_stream("a.txt", nu.Iter([b"x"]))))


# --- mkdir / remove ---------------------------------------------------------


def test_mkdir_many_and_idempotent(go, root):
    term = data.mkdir("one", "two/three")
    go(on(root, nu.Sequential(term, term)))
    assert (root / "one").is_dir()
    assert (root / "two" / "three").is_dir()


def test_mkdir_mode(go, root):
    go(on(root, data.mkdir("locked", mode=0o700)))
    assert (root / "locked").stat().st_mode & 0o777 == 0o700


def test_mkdir_over_a_file_raises(go, root):
    with pytest.raises(FileExistsError):
        go(on(root, data.mkdir("a.txt")))


def test_mkdir_and_remove_take_a_mode_term(go, root):
    go(on(root, data.mkdir("t", mode=nu.Literal(0o750))))
    assert (root / "t").stat().st_mode & 0o777 == 0o750


def test_remove_files_dirs_and_missing(go, root):
    go(on(root, data.remove("a.txt", "empty", "nope")))
    assert not (root / "a.txt").exists()
    assert not (root / "empty").exists()


def test_remove_full_dir_needs_tree(go, root):
    with pytest.raises(OSError):
        go(on(root, data.remove("docs")))
    assert (root / "docs").is_dir()
    go(on(root, data.remove("docs", tree=True)))
    assert not (root / "docs").exists()


def test_remove_a_link_keeps_its_target(go, root):
    (root / "link").symlink_to(root / "a.txt")
    go(on(root, data.remove("link")))
    assert not (root / "link").is_symlink()
    assert (root / "a.txt").exists()


def test_remove_a_link_out_keeps_its_target(go, root, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    (root / "out").symlink_to(outside)
    go(on(root, data.remove("out", tree=True)))
    assert not (root / "out").is_symlink()
    assert (outside / "keep.txt").read_text() == "keep"


@pytest.mark.parametrize("p", [".", "", "docs/..", "./"])
def test_remove_refuses_the_mount(go, root, p):
    with pytest.raises(PermissionError, match="mount itself"):
        go(on(root, data.remove(p, tree=True)))
    assert root.is_dir()


# --- remove_if_holds --------------------------------------------------------


def test_remove_if_holds(go, root):
    (root / "owner").write_text("red 1")
    go(on(root, data.remove_if_holds("owner", "red 2")))
    assert (root / "owner").exists()
    go(on(root, data.remove_if_holds("owner", "red 1")))
    assert not (root / "owner").exists()
    go(on(root, data.remove_if_holds("owner", "red 1")))  # missing: a no-op


def test_remove_if_holds_refuses_the_mount(go, root):
    with pytest.raises(PermissionError):
        go(on(root, data.remove_if_holds(".", "x")))


def test_remove_if_holds_does_not_read_through_a_link_out(go, root, tmp_path):
    secret = tmp_path / "secret"
    secret.write_text("x")
    (root / "owner").symlink_to(secret)
    with pytest.raises(fs.FsEscape):
        go(on(root, data.remove_if_holds("owner", "x")))
    assert secret.exists()


# --- move -------------------------------------------------------------------


def test_move_renames(go, root):
    go(on(root, data.move("a.txt", "b/moved.txt")))
    assert not (root / "a.txt").exists()
    assert (root / "b" / "moved.txt").read_text() == "hello\nworld\n"


def test_move_into_a_dir(go, root):
    go(on(root, data.move("a.txt", "done/")))
    assert (root / "done" / "a.txt").read_text() == "hello\nworld\n"
    go(on(root, data.move("docs", "empty/")))
    assert (root / "empty" / "docs" / "sub" / "deep.md").read_text() == "deep"


def test_move_refuses_a_taken_dst(go, root):
    with pytest.raises(FileExistsError):
        go(on(root, data.move("a.txt", "docs/notes.md")))
    assert (root / "a.txt").exists()
    with pytest.raises(FileExistsError):
        go(on(root, data.move("docs", "empty")))
    assert (root / "docs").is_dir()


def test_move_overwrite(go, root):
    go(on(root, data.move("a.txt", "docs/notes.md", overwrite=True)))
    assert (root / "docs" / "notes.md").read_text() == "hello\nworld\n"
    assert not (root / "a.txt").exists()


def test_move_a_link_moves_the_link(go, root):
    (root / "link").symlink_to("a.txt")
    go(on(root, data.move("link", "docs/link")))
    assert (root / "docs" / "link").is_symlink()
    assert (root / "docs" / "link").readlink().as_posix() == "a.txt"


def test_move_missing_raises(go, root):
    with pytest.raises(FileNotFoundError):
        go(on(root, data.move("nope", "x")))


def test_move_refuses_the_mount(go, root):
    with pytest.raises(PermissionError):
        go(on(root, data.move(".", "x")))
    with pytest.raises(IsADirectoryError):
        go(on(root, data.move("a.txt", ".")))


def test_move_across_devices_copies(root, monkeypatch):
    import errno
    import pathlib

    real = pathlib.Path.rename

    def no_rename(self, target):
        raise OSError(errno.EXDEV, "cross device")

    def no_link(*a, **kw):
        raise OSError(errno.EXDEV, "cross device")

    monkeypatch.setattr(pathlib.Path, "rename", no_rename)
    monkeypatch.setattr(os, "link", no_link)
    nu.run(on(root, nu.Sequential(data.move("a.txt", "x.txt"), data.move("docs", "d2"))))
    monkeypatch.setattr(pathlib.Path, "rename", real)
    assert (root / "x.txt").read_text() == "hello\nworld\n"
    assert not (root / "a.txt").exists()
    assert (root / "d2" / "sub" / "deep.md").read_text() == "deep"
    assert not (root / "docs").exists()


# --- copy -------------------------------------------------------------------


def test_copy(go, root):
    os.utime(root / "a.txt", (1_000_000, 1_000_000))
    go(on(root, data.copy("a.txt", "c/a2.txt")))
    assert (root / "c" / "a2.txt").read_text() == "hello\nworld\n"
    assert (root / "c" / "a2.txt").stat().st_mtime == 1_000_000
    assert (root / "a.txt").exists()
    assert strays(root) == []


def test_copy_into_a_dir_with_verify(go, root):
    go(on(root, data.copy("bin.dat", "backup/", verify=True)))
    assert (root / "backup" / "bin.dat").read_bytes() == bytes(range(256))


def test_copy_verify_mismatch_leaves_no_copy(go, root, monkeypatch):
    real = shutil.copy2

    def bad_copy(src, dst, **kw):
        real(src, dst, **kw)
        with open(dst, "ab") as f:  # noqa: PTH123 - corrupt the copy
            f.write(b"!")

    monkeypatch.setattr(shutil, "copy2", bad_copy)
    with pytest.raises(OSError, match="does not match"):
        go(on(root, data.copy("bin.dat", "out.dat", verify=True)))
    assert not (root / "out.dat").exists()
    assert strays(root) == []


def test_copy_refuses_a_taken_dst_unless_overwrite(go, root):
    with pytest.raises(FileExistsError):
        go(on(root, data.copy("a.txt", "docs/notes.md")))
    assert (root / "docs" / "notes.md").read_text() == "notes"
    go(on(root, data.copy("a.txt", "docs/notes.md", overwrite=True)))
    assert (root / "docs" / "notes.md").read_text() == "hello\nworld\n"
    assert strays(root) == []


def test_copy_refuses_a_dir(go, root):
    with pytest.raises(IsADirectoryError):
        go(on(root, data.copy("docs", "d2")))


# --- touch / make_temp ------------------------------------------------------


def test_touch_makes_and_keeps(go, root):
    os.utime(root / "a.txt", (1_000_000, 1_000_000))
    go(on(root, nu.Sequential(data.touch("a.txt"), data.touch("flags/ready"))))
    assert (root / "a.txt").read_text() == "hello\nworld\n"
    assert (root / "a.txt").stat().st_mtime > 1_000_000
    assert (root / "flags" / "ready").read_bytes() == b""


def test_make_temp_mints_per_run(go, root):
    term = data.make_temp("job-", "jobs")
    a, b = go(on(root, term)), go(on(root, term))
    assert isinstance(a, PurePosixPath)
    assert a != b
    assert a.parent == PurePosixPath("jobs")
    assert a.name.startswith("job-")
    assert (root / a).is_dir()
    assert (root / b).is_dir()


def test_make_temp_feeds_a_write(go, root):
    body = nu.let(
        data.make_temp("job-", "jobs"),
        lambda d: (data.file(d) / "in.txt").write_text("x"),
    )
    go(on(root, body))
    (made,) = (root / "jobs").iterdir()
    assert (made / "in.txt").read_text() == "x"


# --- FileRef verbs ----------------------------------------------------------


def test_file_ref_writes(go, root):
    notes = data / "notes"
    body = nu.Sequential(
        notes.mkdir(),
        (notes / "a.md").write_text("a"),
        (notes / "b.bin").write_bytes(b"b"),
        (notes / "s.bin").write_stream(nu.Iter([b"s1", b"s2"])),
        (notes / "log").append("1"),
        (notes / "log").append_stream(nu.Iter(["2"])),
        (notes / "ready").touch(),
        (notes / "a.md").copy(notes / "a2.md"),
        (notes / "b.bin").move("moved/"),
        (notes / "gone").write_text("x"),
        (notes / "gone").remove(),
        (notes / "own").write_text("me"),
        (notes / "own").remove_if_holds("me"),
        (data / "junk").mkdir(),
        (data / "junk").remove(tree=True),
    )
    go(on(root, body))
    base = root / "notes"
    assert (base / "a.md").read_text() == "a"
    assert (base / "a2.md").read_text() == "a"
    assert (root / "moved" / "b.bin").read_bytes() == b"b"
    assert (base / "s.bin").read_bytes() == b"s1s2"
    assert (base / "log").read_text() == "12\n"
    assert (base / "ready").exists()
    assert not (base / "gone").exists()
    assert not (base / "own").exists()
    assert not (root / "junk").exists()


def test_file_ref_make_temp_inside_it(go, root):
    got = go(on(root, (data / "jobs").make_temp("j-")))
    assert got.parent == PurePosixPath("jobs")
    assert (root / got).is_dir()


def test_file_ref_dst_on_another_mount_is_refused():
    other = fs.FsRef("other")
    with pytest.raises(ValueError, match="another mount"):
        (data / "a").move(other / "b")


def test_file_ref_dst_on_the_same_tag_is_taken():
    again = fs.FsRef("data")
    (data / "a").copy(again / "b")


# --- readonly, escape, unbound ----------------------------------------------


WRITES = [
    data.write_text("w.txt", "x"),
    data.write_bytes("w.bin", b"x"),
    data.write_stream("w.bin", nu.Iter([b"x"])),
    data.append("a.txt", "x"),
    data.append_stream("a.txt", nu.Iter(["x"])),
    data.mkdir("d"),
    data.remove("a.txt"),
    data.remove_if_holds("a.txt", "hello\nworld\n"),
    data.move("a.txt", "b.txt"),
    data.copy("a.txt", "b.txt"),
    data.touch("a.txt"),
    data.make_temp(),
]


@pytest.mark.parametrize("term", WRITES, ids=lambda t: type(t).__name__)
def test_readonly_refuses_every_write(go, root, term):
    before = names(root)
    with pytest.raises(fs.FsReadOnly):
        go(on(root, term, readonly=True))
    assert names(root) == before
    assert (root / "a.txt").read_text() == "hello\nworld\n"


ESCAPES = [
    data.write_text("/abs.txt", "x"),
    data.write_bytes("../up.bin", b"x"),
    data.write_stream("docs/../../up.bin", nu.Iter([b"x"])),
    data.append("out/log", "x"),
    data.mkdir("out/new"),
    data.touch("out/t"),
    data.remove("out/keep.txt"),
    data.move("a.txt", "out/"),
    data.move("out/keep.txt", "here.txt"),
    data.copy("out/keep.txt", "here.txt"),
    data.copy("a.txt", "out/a.txt"),
    data.make_temp("t-", "out"),
]


@pytest.mark.parametrize("term", ESCAPES, ids=lambda t: type(t).__name__)
def test_writes_refuse_an_escape(go, root, tmp_path, term):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    (root / "out").symlink_to(outside)
    with pytest.raises(fs.FsEscape):
        go(on(root, term))
    assert names(outside) == ["keep.txt"]
    assert not (tmp_path / "up.bin").exists()
    assert not (tmp_path / "abs.txt").exists()


def test_writes_under_follow_any_may_leave(go, root, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "out").symlink_to(outside)
    go(on(root, data.write_text("out/x.txt", "x"), follow="any"))
    assert (outside / "x.txt").read_text() == "x"


def test_writes_under_follow_never_refuse_any_link(go, root):
    (root / "inner").symlink_to(root / "docs")
    with pytest.raises(fs.FsEscape):
        go(on(root, data.write_text("inner/x.txt", "x"), follow="never"))


def test_unbound_write_hints_the_tag(go):
    with pytest.raises(RuntimeError, match=r"fs.mount\(..., tag='data'\)"):
        go(data.write_text("a.txt", "x"))


def test_digest_after_write(go, root):
    go(on(root, data.write_bytes("d.bin", b"abc")))
    assert go(on(root, data.digest("d.bin"))) == hashlib.sha256(b"abc").hexdigest()


def test_write_trees_travel_on_the_wire(go, root):
    from nu.lang import wire

    body = nu.Sequential(
        data.mkdir("w1", "w2", mode=0o750),
        (data / "w1" / "a.txt").write_text("a"),
        data.remove("w2", tree=True),
    )
    go(wire.loads(wire.dumps(on(root, body))))
    assert (root / "w1" / "a.txt").read_text() == "a"
    assert not (root / "w2").exists()


@pytest.mark.parametrize(
    ("mode", "max_parallel", "seen"),
    [
        ("sync", 1, "serial"),
        ("sync", 4, "overlap"),
        ("async", 1, "overlap"),
        ("async", 4, "overlap"),
    ],
)
def test_parallel_writes_to_one_mount_are_not_serialized(
    root, monkeypatch, mode, max_parallel, seen
):
    """What the engine does today with two writes to one mount in a Parallel.

    Both declare ``mutates`` on the same ``FsRef``, yet nothing orders them:
    a sync run is serial only because ``max_parallel=1`` runs arms in turn,
    and an async run overlaps them even then, each write in its own thread.
    Writes to one file that must not interleave take an ``fs.Lock``.
    """
    import asyncio
    import time

    real = fabric_mod.FsFabric.write
    spans = []

    def slow(self, *args, **kwargs):
        began = time.monotonic()
        time.sleep(0.2)
        spans.append((began, time.monotonic()))
        return real(self, *args, **kwargs)

    monkeypatch.setattr(fabric_mod.FsFabric, "write", slow)
    term = on(root, nu.Parallel(data.write_text("p1.txt", "1"), data.write_text("p2.txt", "2")))
    if mode == "sync":
        nu.run(term, max_parallel=max_parallel)
    else:
        asyncio.run(nu.arun(term, max_parallel=max_parallel))
    (_, first_end), (second_start, _) = sorted(spans)
    assert ("overlap" if second_start < first_end else "serial") == seen
    assert (root / "p1.txt").read_text() == "1"
    assert (root / "p2.txt").read_text() == "2"
