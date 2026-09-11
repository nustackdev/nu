"""Tests for nu.inspect.core.contract - the shared laws, with no kind involved.

Absence is not a violation. A section that is not written is empty data on
the record; only a written section that lies about the code or about the
format is checked here.
"""

from __future__ import annotations

from nu.inspect.core.contract import (
    Arg,
    call_form,
    check_args,
    check_example,
    check_summary,
    render_args,
)
from nu.inspect.core.docstring import split_docstring


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
        ("second", "the second one.", "'x'"),
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


def test_the_signature_carries_annotation_and_keyword_only_through() -> None:
    class Target:
        """Summary."""

        def __init__(self, first: int, *, flag: bool = False) -> None: ...

    first, flag = call_form(Target, split_docstring(Target.__doc__))
    assert (first.annotation, first.keyword_only, first.has_default) == ("int", False, False)
    assert (flag.annotation, flag.keyword_only, flag.has_default) == ("bool", True, True)


def test_no_default_and_a_default_of_empty_string_are_told_apart() -> None:
    class Target:
        """Summary."""

        def __init__(self, first: object, second: object = "") -> None: ...

    first, second = call_form(Target, split_docstring(Target.__doc__))
    assert (first.default, first.has_default) == ("", False)
    assert (second.default, second.has_default) == ("''", True)


def test_the_receiver_is_dropped_only_when_the_caller_says_it_is_one() -> None:
    class Target:
        """Summary."""

        def inc(self, step: object = 1) -> None: ...

    blocks = split_docstring(Target.inc.__doc__)
    assert [a.name for a in call_form(Target.inc, blocks)] == ["self", "step"]
    assert [a.name for a in call_form(Target.inc, blocks, receiver=True)] == ["step"]


# --- rendering -----------------------------------------------------------


def test_a_call_form_renders_defaults_and_the_variadic_tail() -> None:
    args = (
        Arg(name="source"),
        Arg(name="key", default="'item'", has_default=True),
    )
    assert render_args("Filter", args) == "Filter(source, key='item')"
    assert render_args("Add", (Arg(name="children", variadic=True),)) == "Add(*children)"
    assert render_args("Now", ()) == "Now()"


# --- laws ---------------------------------------------------------------


def test_summary_absence_is_not_a_violation() -> None:
    assert check_summary("x", _blocks("")) == []


def test_summary_rules_when_present() -> None:
    assert [v.rule for v in check_summary("x", _blocks("No full stop"))] == ["summary-unterminated"]
    assert [v.rule for v in check_summary("x", _blocks("A" * 90 + "."))] == ["summary-too-long"]
    assert check_summary("x", _blocks("Fine.")) == []


def test_args_absence_is_not_a_violation() -> None:
    assert check_args("x", _blocks("Summary."), None) == []
    assert check_args("x", _blocks("Summary."), 2) == []
    assert check_args("x", _blocks("Summary."), 0) == []


def test_args_when_written_are_checked_against_the_code() -> None:
    blocks = _blocks("Summary.\n\nArgs:\n    left: one.\n    right: two.\n")
    assert check_args("x", blocks, 2) == []
    (v,) = check_args("x", blocks, 3)
    assert v.rule == "args-arity-mismatch"
    assert v.detail == "documents 2, code takes 3"


def test_a_variadic_arg_skips_the_count_check() -> None:
    blocks = _blocks("Summary.\n\nArgs:\n    *children: many.\n")
    assert check_args("x", blocks, 2) == []


def test_example_absence_is_not_a_violation() -> None:
    assert check_example("x", _blocks("Summary.")) == []


def test_example_rules_when_present() -> None:
    assert [v.rule for v in check_example("x", _blocks("Summary.\n\nExample:\n    f(1\n"))] == [
        "example-unparseable"
    ]
    assert [
        v.rule for v in check_example("x", _blocks("Summary.\n\nExample:\n    >>> f(1)\n"))
    ] == ["example-no-value"]
    assert check_example("x", _blocks("Summary.\n\nExample:\n    f(1)\n")) == []
    assert check_example("x", _blocks("Summary.\n\nExample:\n    >>> f(1)\n    2\n")) == []
