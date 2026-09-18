"""Tests for nu.inspect.module - a module's own docstring, read like any other.

The module docstring is the one written thing a page or a prompt opens with,
so it goes through the same split every subject does rather than being read
raw wherever somebody needs it.
"""

from __future__ import annotations

import types

import nu.core.arithmetic as arithmetic
from nu.inspect import ModuleRecord, Record, parse_module


def test_a_module_record_is_a_record() -> None:
    record = parse_module(arithmetic)
    assert isinstance(record, ModuleRecord)
    assert isinstance(record, Record)


def test_name_is_the_last_part_and_path_and_module_are_the_dotted_name() -> None:
    record = parse_module(arithmetic)
    assert record.name == "arithmetic"
    assert record.path == "nu.core.arithmetic"
    assert record.module == "nu.core.arithmetic"


def test_the_docstring_splits_into_the_same_four_written_fields() -> None:
    module = types.ModuleType("_doc")
    module.__doc__ = (
        "A one line summary.\n"
        "\n"
        "A paragraph of description.\n"
        "\n"
        "Notes:\n"
        "    - One discrete fact.\n"
        "\n"
        "Example:\n"
        "    >>> f(1)\n"
        "    2\n"
    )

    record = parse_module(module)
    assert record.summary == "A one line summary."
    assert record.description == "A paragraph of description."
    assert record.notes == ("One discrete fact.",)
    assert record.example.code == "f(1)"
    assert record.example.expected == "2"


def test_a_module_without_a_docstring_is_absence_not_an_error() -> None:
    record = parse_module(types.ModuleType("_bare"))
    assert record.summary == ""
    assert record.notes == ()
    assert record.examples == ()
