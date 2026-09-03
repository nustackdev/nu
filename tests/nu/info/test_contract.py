"""Tests for nu.info.core.contract - the shared rules, with no kind involved."""

from __future__ import annotations

from nu.info.core.contract import (
    call_form,
    check_args,
    check_example,
    check_summary,
    check_yields,
)
from nu.info.core.docstring import split_docstring


def _blocks(text: str) -> object:
    return split_docstring(text)


# --- call form -----------------------------------------------------------


def test_the_signature_wins_on_structure_and_the_docstring_supplies_prose() -> None:
    class Target:
        """Summary.

        Args:
            first: the first one.
            second: the second one.
        """

        def __init__(self, first: object, second: object = "x") -> None: ...

    args = call_form(Target, split_docstring(Target.__doc__))
    assert [(a.name, a.text, a.default) for a in args] == [
        ("first", "the first one.", ""),
        ("second", "the second one.", "x"),
    ]


def test_the_docstring_stands_alone_when_the_signature_says_nothing() -> None:
    class Target:
        """Summary.

        Args:
            left: one.
            right: two.
        """

    args = call_form(Target, split_docstring(Target.__doc__))
    assert [a.name for a in args] == ["left", "right"]
    assert not any(a.variadic for a in args)


def test_a_variadic_documented_arg_survives_the_merge() -> None:
    class Target:
        """Summary.

        Args:
            *children: the values.
        """

    (arg,) = call_form(Target, split_docstring(Target.__doc__))
    assert (arg.name, arg.variadic) == ("children", True)


def test_no_source_at_all_is_absence_not_zero() -> None:
    assert call_form(object(), split_docstring("Summary.")) == ()


# --- checks --------------------------------------------------------------


def test_summary_rules() -> None:
    assert [p.rule for p in check_summary("x", _blocks(""))] == ["summary-missing"]
    assert [p.rule for p in check_summary("x", _blocks("No full stop"))] == ["summary-unterminated"]
    assert [p.rule for p in check_summary("x", _blocks("A" * 90 + "."))] == ["summary-too-long"]
    assert check_summary("x", _blocks("Fine.")) == []


def test_args_missing_unless_provably_nothing_is_taken() -> None:
    assert [p.rule for p in check_args("x", _blocks("Summary."), None)] == ["args-missing"]
    assert [p.rule for p in check_args("x", _blocks("Summary."), 2)] == ["args-missing"]
    assert check_args("x", _blocks("Summary."), 0) == []


def test_args_are_checked_against_the_count_the_code_gives() -> None:
    blocks = _blocks("Summary.\n\nArgs:\n    left: one.\n    right: two.\n")
    assert check_args("x", blocks, 2) == []
    (problem,) = check_args("x", blocks, 3)
    assert problem.rule == "args-arity-mismatch"
    assert problem.detail == "documents 2, code takes 3"


def test_a_variadic_arg_skips_the_count_check() -> None:
    blocks = _blocks("Summary.\n\nArgs:\n    *children: many.\n")
    assert check_args("x", blocks, 2) == []


def test_yields_is_required_when_asked_for() -> None:
    assert [p.rule for p in check_yields("x", _blocks("Summary."))] == ["yields-missing"]
    assert check_yields("x", _blocks("Summary.\n\nYields:\n    A value.\n")) == []


def test_example_rules() -> None:
    assert [p.rule for p in check_example("x", _blocks("Summary."))] == ["example-missing"]
    assert [p.rule for p in check_example("x", _blocks("Summary.\n\nExample:\n    f(1\n"))] == [
        "example-unparseable"
    ]
    assert [p.rule for p in check_example("x", _blocks("Summary.\n\nExample:\n    f(1)\n"))] == [
        "example-not-doctest"
    ]
    assert [
        p.rule for p in check_example("x", _blocks("Summary.\n\nExample:\n    >>> f(1)\n"))
    ] == ["example-no-value"]
    assert check_example("x", _blocks("Summary.\n\nExample:\n    >>> f(1)\n    2\n")) == []
