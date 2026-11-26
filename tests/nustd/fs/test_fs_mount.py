"""Mounts: the presets, tags, temp dirs, the unbound hint and pickling."""

from __future__ import annotations

import pickle
import stat
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, cast

import pytest

import nu
import nustd
from nu.lang import wire
from nustd import fs


if TYPE_CHECKING:
    from collections.abc import Callable


data = fs.FsRef("data")
plain = fs.FsRef()


def test_registered_as_a_lazy_fabric():
    assert "fs" in dir(nustd)
    assert nustd.fs.FsRef is fs.FsRef


def test_is_a_fabric_ref_over_the_fs_fabric():
    assert isinstance(data, nu.context.FabricRef)
    assert fs.FsRef.fabric is fs.FsFabric


def test_ref_reads_the_bound_fabric(go, root):
    got = go(fs.mount(root, tag="data", body=data))
    assert isinstance(got, fs.FsFabric)
    assert got.readonly is False


def test_untagged_mount(go, root):
    assert go(fs.mount(root, body=plain.read_text("a.txt"))) == "hello\nworld\n"


def test_tag_from_a_ref(go, root):
    assert go(fs.mount(root, tag=data, body=data.read_text("a.txt"))) == "hello\nworld\n"
    assert go(fs.mount(root, tag=plain, body=plain.has("a.txt"))) is True


def test_computed_tag(go, root):
    ref = fs.FsRef(nu.Literal("data"))
    assert go(fs.mount(root, tag=nu.Literal("data"), body=ref.has("a.txt"))) is True


def test_bad_tag_is_refused():
    with pytest.raises(TypeError, match="tag"):
        fs.FsRef(3)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="tag"):
        fs.mount("/tmp", tag=3)  # type: ignore[arg-type]


def test_two_mounts_in_one_tree(go, root, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    (other / "a.txt").write_text("other")
    o = fs.FsRef("other")
    app = fs.mount(
        root,
        tag="data",
        body=fs.mount(
            other, tag="other", body=nu.List.of(data.read_text("a.txt"), o.read_text("a.txt"))
        ),
    )
    assert go(app) == ["hello\nworld\n", "other"]


def test_exists(go, root):
    assert go(data.exists()) is False
    assert go(fs.mount(root, tag="data", body=data.exists())) is True
    assert go(fs.mount(root, body=data.exists())) is False
    assert go(fs.mount(root, body=plain.exists())) is True


def test_unbound_hint_names_the_tag(go):
    with pytest.raises(
        RuntimeError, match=r"no fs mount 'data' bound; wrap with fs.mount\(\.\.\., tag='data'\)"
    ):
        go(data.read_text("a.txt"))


def test_unbound_hint_untagged(go):
    with pytest.raises(RuntimeError, match="no fs mount bound"):
        go(plain.read_text("a.txt"))


def test_tagged_ref_never_falls_back_to_the_untagged_mount(go, root):
    with pytest.raises(RuntimeError, match="'data'"):
        go(fs.mount(root, body=data.read_text("a.txt")))


def test_mount_creates_a_missing_dir(go, tmp_path):
    where = tmp_path / "new" / "deeper"
    assert go(fs.mount(where, body=plain.has("."))) is True
    assert where.is_dir()


def test_mount_mode_on_create(go, tmp_path):
    where = tmp_path / "moded"
    go(fs.mount(where, mode=0o700, body=plain.has(".")))
    assert stat.S_IMODE(where.stat().st_mode) == 0o700


def test_mount_without_create_refuses_a_missing_dir(go, tmp_path):
    with pytest.raises(FileNotFoundError, match="create is off"):
        go(fs.mount(tmp_path / "nope", create=False, body=plain.has(".")))
    assert not (tmp_path / "nope").exists()


def test_mount_of_a_file_is_refused(go, root):
    with pytest.raises(NotADirectoryError):
        go(fs.mount(root / "a.txt", body=plain.has(".")))


def test_mount_resolves_a_relative_path_at_entry(go, root, monkeypatch):
    monkeypatch.chdir(root.parent)
    assert go(fs.mount("root", body=plain.read_text("a.txt"))) == "hello\nworld\n"


def test_readonly_flag_reaches_the_fabric(go, root):
    assert go(fs.mount(root, readonly=True, body=plain)).readonly is True


def test_root_outside_the_bracket_raises():
    fabric = fs.FsFabric(path="/tmp")
    with pytest.raises(RuntimeError, match="not open"):
        _ = fabric.root


def test_fabric_needs_a_path_or_temp():
    with pytest.raises(ValueError, match="path"):
        fs.FsFabric()


# --- tmp --------------------------------------------------------------------


def test_tmp_makes_a_fresh_dir_and_removes_it(go):
    where = Path(go(fs.tmp(body=plain.where())))
    assert where.name.startswith("nu-")
    assert not where.exists()


def test_tmp_prefix_and_keep(go):
    where = Path(go(fs.tmp(prefix="fs-test-", keep=True, body=plain.where())))
    try:
        assert where.name.startswith("fs-test-")
        assert where.is_dir()
    finally:
        where.rmdir()


def test_tmp_is_removed_when_the_body_raises(go):
    seen: list[str] = []

    class BoomError(Exception):
        pass

    def grab(path):
        seen.append(path)
        raise BoomError

    body = cast("Callable[..., nu.Nu]", nu.host(grab))(plain.where())
    with pytest.raises(BoomError):
        go(fs.tmp(body=body))
    assert seen
    assert not Path(seen[0]).exists()


def test_tmp_tagged(go):
    scratch = fs.FsRef("scratch")
    assert go(fs.tmp(tag="scratch", body=scratch.exists())) is True


def test_each_run_gets_its_own_tmp(go):
    app = fs.tmp(body=plain.where())
    assert go(app) != go(app)


# --- tmp with a lambda body -------------------------------------------------


def _isdir(path: str) -> bool:
    return Path(path).is_dir()


isdir = cast("Callable[..., nu.Nu]", nu.host(_isdir))


def test_tmp_lambda_gets_the_path(go):
    where, there = go(fs.tmp(prefix="fs-root-", body=lambda root: nu.List.of(root, isdir(root))))
    assert Path(where).is_absolute()
    assert Path(where).name.startswith("fs-root-")
    assert there is True
    assert not Path(where).exists()


def test_tmp_lambda_path_is_the_mount(go):
    assert go(fs.tmp(body=lambda root: nu.Eq(root, plain.where()))) is True


def test_tmp_lambda_on_a_tagged_mount(go):
    scratch = fs.FsRef("scratch")
    app = fs.tmp(tag="scratch", body=lambda root: nu.Eq(root, scratch.where()))
    assert go(app) is True


def test_tmp_tree_body_is_handed_no_path(go):
    assert go(fs.tmp(body=nu.Eq(plain.where(), plain.where()))) is True


def test_tmp_lambda_of_no_parameter_is_a_tree(go):
    assert go(fs.tmp(body=lambda: isdir(plain.where()))) is True


def test_tmp_lambda_of_two_parameters_is_refused():
    with pytest.raises(TypeError, match="at most 1"):
        fs.tmp(body=lambda root, other: root)


def test_tmp_path_frame_stays_inside_the_body(go):
    # Two tmps over one lambda: each reads its own dir, the inner shadowing the outer.
    def body(root: nu.Nu) -> nu.Nu:
        return nu.List.of(root, fs.tmp(prefix="inner-", body=lambda inner: inner), root)

    outer, inner, again = go(fs.tmp(prefix="outer-", body=body))
    assert outer == again
    assert Path(outer).name.startswith("outer-")
    assert Path(inner).name.startswith("inner-")


def test_tmp_lambda_travels_on_the_wire(go):
    app = wire.loads(wire.dumps(fs.tmp(body=lambda root: isdir(root))))
    assert go(app) is True


# --- pickling ---------------------------------------------------------------


def test_refs_and_file_refs_pickle():
    for obj in (data, plain, data / "a" / "b"):
        back = pickle.loads(pickle.dumps(obj))  # noqa: S301 - our own bytes
        assert type(back) is type(obj)
    f = pickle.loads(pickle.dumps(data / "a" / "b"))  # noqa: S301 - our own bytes
    assert f.p == PurePosixPath("a/b")
    assert isinstance(f.fs, fs.FsRef)


def test_a_file_ref_with_a_term_part_pickles():
    f = pickle.loads(pickle.dumps(data / nu.Literal("x") / "y"))  # noqa: S301 - our own bytes
    assert isinstance(f, fs.FileRef)


def test_presets_travel_on_the_wire(go, root):
    app = fs.mount(root, tag="data", follow="never", body=(data / "a.txt").read_text())
    assert go(wire.loads(wire.dumps(app))) == "hello\nworld\n"
    scratch = wire.loads(wire.dumps(fs.tmp(body=plain.has("."))))
    assert go(scratch) is True


def test_errors_pickle():
    err = pickle.loads(pickle.dumps(fs.FsLocked("held", {"pid": 1})))  # noqa: S301 - our own bytes
    assert err.holder == {"pid": 1}
    assert str(err) == "held"
    assert isinstance(pickle.loads(pickle.dumps(fs.FsEscape("x"))), fs.FsEscape)  # noqa: S301
