"""Tests that form slicing (form[a:b:c]) compiles and evaluates correctly.

Covers Str, Bytes, and List slices through the fixed
GetItem(self, Slice(start, stop, step)) composition.
"""

from __future__ import annotations

from nu.forms import Bytes, List, Str
from nu.lang.helpers import compile, eval
from nu.lang.runtime import Context


def val(term: object) -> object:
    return eval(compile(term), Context())[0]


# --- Str slicing --------------------------------------------------------


def test_str_slice_start_stop():
    assert val(Str("hello world")[1:5]) == "ello"


def test_str_slice_stop_only():
    assert val(Str("hello")[:3]) == "hel"


def test_str_slice_step():
    assert val(Str("abcdef")[::2]) == "ace"


def test_str_slice_start_stop_step():
    assert val(Str("abcdefgh")[1:7:2]) == "bdf"


def test_str_slice_negative_step():
    assert val(Str("hello")[::-1]) == "olleh"


# --- Bytes slicing -------------------------------------------------------


def test_bytes_slice_start_stop():
    assert val(Bytes(b"hello world")[1:5]) == b"ello"


def test_bytes_slice_stop_only():
    assert val(Bytes(b"hello")[:3]) == b"hel"


def test_bytes_slice_step():
    assert val(Bytes(b"abcdef")[::2]) == b"ace"


# --- List slicing --------------------------------------------------------


def test_list_slice_start_stop():
    assert val(List([0, 1, 2, 3, 4])[1:4]) == [1, 2, 3]


def test_list_slice_stop_only():
    assert val(List([10, 20, 30, 40])[:2]) == [10, 20]


def test_list_slice_step():
    assert val(List([0, 1, 2, 3, 4, 5])[::2]) == [0, 2, 4]


def test_list_slice_all_none():
    # [:] returns a copy of the full list
    assert val(List([1, 2, 3])[:]) == [1, 2, 3]


# --- SliceableForm.slice() method -------------------------------------------


def test_list_slice_method():
    # List inherits SliceableForm.slice() for named-argument slicing
    assert val(List([0, 1, 2, 3, 4]).slice(1, 4)) == [1, 2, 3]
