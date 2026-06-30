"""Functional tests for ``nu.std.pathlib`` - drive the Forms through the engine.

Covers every pure modeling path: constructors and method calls (factory atoms),
property reads (core ``GetAttrQuery``), the ``/`` operator, comparison (core
atoms), and the async path. Results are asserted against real ``pathlib``.
"""

from __future__ import annotations

import asyncio
import pathlib as pypath

from nu.lang.helpers import arun, run
from nu.std.pathlib import Path


# --- property reads (core GetAttrQuery) ---------------------------------


def test_path_name() -> None:
    assert run(Path.of("usr", "local", "bin").name())[0] == "bin"


def test_path_suffix() -> None:
    assert run(Path.of("archive.tar.gz").suffix())[0] == ".gz"


def test_path_suffixes() -> None:
    assert run(Path.of("archive.tar.gz").suffixes())[0] == [".tar", ".gz"]


def test_path_parts() -> None:
    expected = pypath.PurePath("usr", "local").parts
    assert run(Path.of("usr", "local").parts())[0] == expected


def test_path_parent() -> None:
    value, _ = run(Path.of("a", "b", "c").parent().as_posix())
    assert value == pypath.PurePath("a", "b", "c").parent.as_posix()


# --- method calls (factory atoms over unbound PurePath methods) ---------


def test_path_with_suffix() -> None:
    value, _ = run(Path.of("report.txt").with_suffix(".md").as_posix())
    assert value == pypath.PurePath("report.txt").with_suffix(".md").as_posix()


def test_path_with_name() -> None:
    value, _ = run(Path.of("a", "b.txt").with_name("c.md").as_posix())
    assert value == pypath.PurePath("a", "b.txt").with_name("c.md").as_posix()


def test_path_joinpath() -> None:
    value, _ = run(Path.of("etc").joinpath("nginx", "nginx.conf").as_posix())
    assert value == pypath.PurePath("etc").joinpath("nginx", "nginx.conf").as_posix()


def test_path_relative_to() -> None:
    value, _ = run(Path.of("a", "b", "c").relative_to("a").as_posix())
    assert value == pypath.PurePath("a", "b", "c").relative_to("a").as_posix()


def test_path_is_absolute() -> None:
    assert run(Path.of("/etc", "hosts").is_absolute())[0] is True
    assert run(Path.of("etc", "hosts").is_absolute())[0] is False


def test_path_match() -> None:
    assert run(Path.of("a", "b.py").match("*.py"))[0] is True


# --- the / operator (joinpath atom) -------------------------------------


def test_path_truediv() -> None:
    value, _ = run((Path.of("etc") / "nginx" / "nginx.conf").as_posix())
    assert value == (pypath.PurePath("etc") / "nginx" / "nginx.conf").as_posix()


# --- comparison (core atoms) --------------------------------------------


def test_path_comparison() -> None:
    assert run(Path.of("a") < Path.of("b"))[0] is True


def test_path_eq() -> None:
    assert run(Path.of("a", "b").eq(Path.of("a", "b")))[0] is True


# --- conversions --------------------------------------------------------


def test_path_as_posix() -> None:
    value, _ = run(Path.of("a", "b", "c").as_posix())
    assert value == pypath.PurePath("a", "b", "c").as_posix()


# --- constructor that reads the environment -----------------------------


def test_cwd_returns_a_path() -> None:
    value, _ = run(Path.cwd())
    assert isinstance(value, pypath.PurePath)


# --- async path ---------------------------------------------------------


def test_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(Path.of("usr", "bin").as_posix()))
    assert value == pypath.PurePath("usr", "bin").as_posix()
