"""Tests for nu.info.interaction: parser and verifier.

Absence is not a violation. The verifier only catches written facts that lie
about the code or malformed sections; missing sections are empty fields on
the record.
"""

from __future__ import annotations

import nu.core as core
import nu.flows as flows
from nu.core import Add, Filter, Map, Sub
from nu.flows import IfDo
from nu.info import catalogue, parse_interaction, verify_interaction
from nu.info.interaction import unpacked_arity


# --- verifier ------------------------------------------------------------


class _NoDoc:
    pass


class _SummaryOnly:
    """A summary and nothing else."""


class _Unterminated:
    """A summary with no full stop

    Args:
        only: the one child.
    """


class _Mismatch:
    """A summary.

    Args:
        left: one.
        right: two.
        extra: three, which the code does not take.
    """

    def _compile(self, nid: int, children: tuple[object, ...]) -> object:
        left, right = children
        return left, right


def test_no_docstring_is_absence_not_a_violation() -> None:
    assert verify_interaction(_NoDoc) == []


def test_a_summary_alone_reports_nothing() -> None:
    assert verify_interaction(_SummaryOnly) == []


def test_unterminated_summary_is_reported_with_the_text() -> None:
    (violation,) = verify_interaction(_Unterminated)
    assert violation.rule == "summary-unterminated"
    assert violation.detail == "A summary with no full stop"


def test_documented_arity_is_checked_against_what_compile_unpacks() -> None:
    (violation,) = verify_interaction(_Mismatch)
    assert violation.rule == "args-arity-mismatch"
    assert violation.detail == "documents 3, code takes 2"


def test_verification_never_raises_on_a_real_atom() -> None:
    for record in catalogue(core):
        assert isinstance(verify_interaction(record.target), list)


# --- parser --------------------------------------------------------------


def test_record_head_of_a_real_atom() -> None:
    record = parse_interaction(Add, path="nu.core.Add")
    assert record.name == "Add"
    assert record.path == "nu.core.Add"
    assert record.summary == "The sum of its scalar children."


def test_a_docstring_with_no_sections_is_empty_not_a_crash() -> None:
    record = parse_interaction(_SummaryOnly)
    assert not record.example
    assert record.notes == ()
    assert record.yields == ""
    assert record.args == ()


def test_a_description_is_read_when_there_is_one() -> None:
    class _WithMechanism:
        """A summary.

        Walks the source and folds each item into an accumulator, which is
        the mechanism a summary cannot carry.

        Notes:
            - A discrete fact, kept apart from the paragraph above.
        """

    record = parse_interaction(_WithMechanism)
    assert record.description.startswith("Walks the source")
    assert record.notes == ("A discrete fact, kept apart from the paragraph above.",)


def test_record_taxonomy_comes_off_the_kinds_module() -> None:
    add = parse_interaction(Add)
    assert (add.kind, add.sort, add.cardinality) == ("ScalarQuery", "scalar_query", "scalar")
    do = parse_interaction(IfDo)
    assert (do.kind, do.sort, do.cardinality) == ("Control", "control", "void")


def test_args_come_from_a_declared_constructor_when_there_is_one() -> None:
    record = parse_interaction(Filter)
    assert [arg.name for arg in record.args] == ["source", "predicate", "key"]
    assert record.required == 2
    assert record.arity == 3


def test_a_default_is_read_off_the_code_not_the_prose() -> None:
    (key,) = [arg for arg in parse_interaction(Map).args if arg.name == "key"]
    assert key.default == "item"


def test_a_variadic_atom_has_no_arity() -> None:
    record = parse_interaction(Add)
    assert [arg.name for arg in record.args] == ["children"]
    assert record.arity is None


def test_an_undocumented_atom_has_unknown_arity_not_zero() -> None:
    record = parse_interaction(_SummaryOnly)
    assert record.args == ()
    assert record.arity is None


def test_record_source_and_docstring_are_lazy_lookups() -> None:
    record = parse_interaction(Add)
    source = record.source()
    assert source is not None
    assert source.text.startswith("class Add(")
    assert record.blocks().raw == Add.__doc__


def test_catalogue_covers_every_exported_interaction() -> None:
    names = {r.name for r in catalogue(core)}
    assert {"Add", "Map", "Sum", "Print", "Literal"} <= names
    assert all(r.path.startswith("nu.core.") for r in catalogue(core))
    assert {"Sequential", "IfDo", "Race"} <= {r.name for r in catalogue(flows)}


def test_unpacked_arity_recovers_what_the_constructor_hides() -> None:
    assert unpacked_arity(Sub) == 2  # `left, right = children`
    assert unpacked_arity(Add) is None  # folds its children, no unpacking
