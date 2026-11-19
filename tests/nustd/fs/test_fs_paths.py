"""Paths stay inside their mount: absolute, ``..`` and symlinks under each follow rule."""

from __future__ import annotations

from pathlib import PurePosixPath

import pytest

import nu
from nustd import fs


data = fs.FsRef("data")


def on(root, body, **kwargs):
    return fs.mount(root, tag="data", body=body, **kwargs)


@pytest.fixture
def outside(tmp_path):
    """A dir next to the mount, with a secret in it."""
    out = tmp_path / "outside"
    out.mkdir()
    (out / "secret.txt").write_text("secret")
    return out


@pytest.mark.parametrize(
    "bad",
    ["/etc/passwd", "..", "../x", "a/../../x", "docs/../../x", PurePosixPath("/etc"), "./../x"],
)
def test_escapes_are_refused(go, root, bad):
    with pytest.raises(fs.FsEscape):
        go(on(root, data.read_text(bad)))


def test_escape_is_a_permission_error():
    assert issubclass(fs.FsEscape, PermissionError)


@pytest.mark.parametrize("ok", ["docs/../a.txt", "./a.txt", "docs/./../a.txt"])
def test_dot_dot_inside_the_mount_is_fine(go, root, ok):
    assert go(on(root, data.has(ok))) is True


def test_where_refuses_an_escape(go, root):
    with pytest.raises(fs.FsEscape):
        go(on(root, data.where("..")))


def test_nul_byte_is_refused(go, root):
    with pytest.raises(ValueError, match="NUL"):
        go(on(root, data.has("a\x00b")))


def test_path_of_the_wrong_type(go, root):
    with pytest.raises(TypeError, match="fs path"):
        go(on(root, data.has(nu.Literal(3))))


# --- symlinks ---------------------------------------------------------------


def test_inside_follows_a_link_that_stays_in(go, root):
    (root / "ln.txt").symlink_to(root / "a.txt")
    (root / "lndir").symlink_to(root / "docs")
    assert go(on(root, data.read_text("ln.txt"))) == "hello\nworld\n"
    assert go(on(root, data.read_text("lndir/notes.md"))) == "notes"


def test_inside_refuses_a_link_that_leads_out(go, root, outside):
    (root / "out").symlink_to(outside)
    (root / "out.txt").symlink_to(outside / "secret.txt")
    with pytest.raises(fs.FsEscape):
        go(on(root, data.read_text("out/secret.txt")))
    with pytest.raises(fs.FsEscape):
        go(on(root, data.read_text("out.txt")))
    with pytest.raises(fs.FsEscape):
        go(on(root, nu.Collect(data.list("out"))))


def test_relative_link_out_is_refused(go, root, outside):
    (root / "rel").symlink_to("../outside")
    with pytest.raises(fs.FsEscape):
        go(on(root, data.read_text("rel/secret.txt")))


def test_stat_sees_a_link_out_as_a_link(go, root, outside):
    (root / "out.txt").symlink_to(outside / "secret.txt")
    row = go(on(root, data.stat("out.txt")))
    assert row["kind"] == "link"


def test_stat_through_a_link_out_is_refused(go, root, outside):
    (root / "out").symlink_to(outside)
    with pytest.raises(fs.FsEscape):
        go(on(root, data.stat("out/secret.txt")))


def test_never_refuses_every_link(go, root):
    (root / "ln.txt").symlink_to(root / "a.txt")
    (root / "lndir").symlink_to(root / "docs")
    with pytest.raises(fs.FsEscape, match="symlink"):
        go(on(root, data.read_text("ln.txt"), follow="never"))
    with pytest.raises(fs.FsEscape, match="symlink"):
        go(on(root, data.read_text("lndir/notes.md"), follow="never"))
    assert go(on(root, data.read_text("a.txt"), follow="never")) == "hello\nworld\n"


def test_never_still_stats_the_link_itself(go, root):
    (root / "ln.txt").symlink_to(root / "a.txt")
    assert go(on(root, data.stat("ln.txt"), follow="never"))["kind"] == "link"


def test_any_follows_a_link_out(go, root, outside):
    (root / "out").symlink_to(outside)
    assert go(on(root, data.read_text("out/secret.txt"), follow="any")) == "secret"


def test_any_still_refuses_lexical_escapes(go, root):
    with pytest.raises(fs.FsEscape):
        go(on(root, data.read_text("../x"), follow="any"))
    with pytest.raises(fs.FsEscape):
        go(on(root, data.read_text("/etc/hosts"), follow="any"))


def test_bad_follow_is_refused_at_build():
    with pytest.raises(ValueError, match="follow"):
        fs.mount("/tmp", follow="sometimes")


def test_mount_through_a_link_checks_the_real_place(go, root, tmp_path):
    # The mount itself may be reached through a link: the checks run against
    # where it really is, so its own files are inside.
    alias = tmp_path / "alias"
    alias.symlink_to(root)
    assert go(fs.mount(alias, tag="data", body=data.read_text("a.txt"))) == "hello\nworld\n"
    assert go(fs.mount(alias, tag="data", body=data.where())) == str(root.resolve())
