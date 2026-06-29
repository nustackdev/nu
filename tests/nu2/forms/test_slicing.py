"""Tests that form slicing (form[a:b:c]) compiles and evaluates correctly.

Covers StrForm, BytesForm, and ListForm slices through the fixed
GetItemQuery(self, SliceQuery(start, stop, step)) composition.
"""

from __future__ import annotations

from nu2.forms import BytesForm, ListForm, StrForm
from nu2.lang import compile
from nu2.lang.helpers import eval
from nu2.lang.runtime import Context


def val(term: object) -> object:
    return eval(compile(term), Context())[0]


# --- StrForm slicing --------------------------------------------------------


def test_str_slice_start_stop():
    assert val(StrForm("hello world")[1:5]) == "ello"


def test_str_slice_stop_only():
    assert val(StrForm("hello")[:3]) == "hel"


def test_str_slice_step():
    assert val(StrForm("abcdef")[::2]) == "ace"


def test_str_slice_start_stop_step():
    assert val(StrForm("abcdefgh")[1:7:2]) == "bdf"


def test_str_slice_negative_step():
    assert val(StrForm("hello")[::-1]) == "olleh"


# --- BytesForm slicing -------------------------------------------------------


def test_bytes_slice_start_stop():
    assert val(BytesForm(b"hello world")[1:5]) == b"ello"


def test_bytes_slice_stop_only():
    assert val(BytesForm(b"hello")[:3]) == b"hel"


def test_bytes_slice_step():
    assert val(BytesForm(b"abcdef")[::2]) == b"ace"


# --- ListForm slicing --------------------------------------------------------


def test_list_slice_start_stop():
    assert val(ListForm([0, 1, 2, 3, 4])[1:4]) == [1, 2, 3]


def test_list_slice_stop_only():
    assert val(ListForm([10, 20, 30, 40])[:2]) == [10, 20]


def test_list_slice_step():
    assert val(ListForm([0, 1, 2, 3, 4, 5])[::2]) == [0, 2, 4]


def test_list_slice_all_none():
    # [:] returns a copy of the full list
    assert val(ListForm([1, 2, 3])[:]) == [1, 2, 3]


# --- SliceableForm.slice() method -------------------------------------------


def test_list_slice_method():
    # ListForm inherits SliceableForm.slice() for named-argument slicing
    assert val(ListForm([0, 1, 2, 3, 4]).slice(1, 4)) == [1, 2, 3]
