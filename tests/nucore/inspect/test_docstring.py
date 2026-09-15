"""Tests for nu.inspect.core.docstring - what was written, in isolation."""

from __future__ import annotations

from nu.inspect.core.docstring import (
    parse_args,
    parse_example,
    parse_examples,
    parse_notes,
    split_docstring,
)


# --- blocks --------------------------------------------------------------


def test_empty_is_data_not_an_error() -> None:
    blocks = split_docstring(None)
    assert blocks.summary == ""
    assert blocks.sections == ()


def test_summary_and_description() -> None:
    blocks = split_docstring("The sum of its children.\n\nA longer note.\nOn two lines.\n")
    assert blocks.summary == "The sum of its children."
    assert blocks.description == "A longer note.\nOn two lines."


def test_the_raw_text_is_kept() -> None:
    raw = "  Summary.\n\n  Args:\n      x: a thing\n  "
    assert split_docstring(raw).raw == raw


def test_google_sections_are_split_in_order() -> None:
    blocks = split_docstring(
        """Summary.

        Args:
            source: the stream to read
            key: the loop variable name

        Yields:
            The folded value.

        Example:
            Add(1, 2)  # -> 3
        """
    )
    assert [s.name for s in blocks.sections] == ["Args", "Yields", "Example"]
    assert blocks.text_of("Yields") == "The folded value."
    assert blocks.text_of("Example") == "Add(1, 2)  # -> 3"


def test_section_lookup_is_case_insensitive_and_multi_name() -> None:
    blocks = split_docstring("Summary.\n\nExamples:\n    Add(1, 2)\n")
    assert blocks.section("Example", "Examples") is not None
    assert blocks.text_of("Nothing") == ""


def test_a_colon_line_with_trailing_text_is_not_a_section() -> None:
    blocks = split_docstring("Summary.\n\nNote: this is prose, not a section.\n")
    assert blocks.sections == ()
    assert "prose" in blocks.description


# --- args ----------------------------------------------------------------


def test_args_are_read_in_order_with_their_prose() -> None:
    args = parse_args("source: the stream to read\nkey: the loop variable name")
    assert [(a.name, a.text) for a in args] == [
        ("source", "the stream to read"),
        ("key", "the loop variable name"),
    ]


def test_an_arg_description_may_wrap() -> None:
    (arg,) = parse_args("ndigits: how many digits to keep. Optional:\n    omit to round whole.")
    assert arg.text == "how many digits to keep. Optional: omit to round whole."


def test_a_variadic_arg_is_marked_and_unstarred() -> None:
    (arg,) = parse_args("*children: the values to add")
    assert (arg.name, arg.variadic) == ("children", True)


def test_a_type_in_parentheses_is_ignored() -> None:
    (arg,) = parse_args("value (int): the value to hold")
    assert (arg.name, arg.text) == ("value", "the value to hold")


# --- notes ---------------------------------------------------------------


def test_notes_split_into_one_string_per_bullet() -> None:
    assert parse_notes("- First fact.\n- Second fact, which wraps\n  onto another line.") == (
        "First fact.",
        "Second fact, which wraps onto another line.",
    )


def test_prose_notes_are_kept_as_one_entry() -> None:
    assert parse_notes("No bullet marker here.") == ("No bullet marker here.",)


# --- example -------------------------------------------------------------


def test_doctest_form_splits_code_from_its_value() -> None:
    example = parse_example(">>> nu.run(nu.Int(10) - nu.Int(3))[0]\n7")
    assert example.doctest
    assert example.code == "nu.run(nu.Int(10) - nu.Int(3))[0]"
    assert example.expected == "7"


def test_continuation_lines_join_the_code() -> None:
    example = parse_example(">>> nu.run(\n...     nu.Int(1),\n... )\n1")
    assert example.code == "nu.run(\n    nu.Int(1),\n)"
    assert example.expected == "1"


def test_a_plain_snippet_has_no_expected_value() -> None:
    example = parse_example('nu.Print(nu.Str("hi"))')
    assert not example.doctest
    assert example.code == 'nu.Print(nu.Str("hi"))'
    assert example.expected == ""


def test_an_empty_example_is_falsey_data_not_an_error() -> None:
    assert not parse_example("   \n  ")


# --- multiple examples ---------------------------------------------------


def test_a_section_with_one_example_parses_to_one_entry() -> None:
    examples = parse_examples(">>> nu.run(nu.Int(1))[0]\n1")
    assert len(examples) == 1
    assert examples[0].code == "nu.run(nu.Int(1))[0]"
    assert examples[0].expected == "1"


def test_blank_line_separated_examples_split_into_entries() -> None:
    text = ">>> nu.run(nu.Int(1))[0]\n1\n\n>>> nu.run(nu.Int(2) + nu.Int(3))[0]\n5"
    examples = parse_examples(text)
    assert len(examples) == 2
    assert examples[0].expected == "1"
    assert examples[1].code == "nu.run(nu.Int(2) + nu.Int(3))[0]"
    assert examples[1].expected == "5"


def test_a_mixed_section_keeps_doctest_and_plain_chunks_apart() -> None:
    text = ">>> nu.run(nu.Int(1))[0]\n1\n\nnu.Print(nu.Str('side effect'))"
    examples = parse_examples(text)
    assert len(examples) == 2
    assert examples[0].doctest
    assert not examples[1].doctest


def test_an_empty_section_yields_an_empty_tuple() -> None:
    assert parse_examples("") == ()
    assert parse_examples("   \n  \n") == ()
