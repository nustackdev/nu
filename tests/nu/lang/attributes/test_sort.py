"""Unit tests for ``nu.lang.attributes.sort``.

Covers the ``Sort`` enum (structural categories), the composition
``MATRIX`` (allowed child sorts per parent sort), ``subsort`` traversal,
``matrix_sort`` folding, and the synthesized ``has_command`` flag.
"""

from __future__ import annotations

import pytest
from _support.law_terms import Cmd, FlowS, Q, R

from nu.lang import compile as nu_compile
from nu.lang.attributes import Attr, Sort
from nu.lang.attributes.sort import MATRIX, matrix_sort, subsort


# --- subsort ------------------------------------------------------------


@pytest.mark.parametrize(
    "sort",
    list(Sort),
)
def test_subsort_is_reflexive(sort: Sort) -> None:
    assert subsort(sort, sort)


@pytest.mark.parametrize(
    ("sort", "parent"),
    [
        (Sort.QUERY, Sort.INTERACTION),
        (Sort.COMMAND, Sort.INTERACTION),
        (Sort.ACTION, Sort.INTERACTION),
        (Sort.FLOW, Sort.INTERACTION),
        (Sort.SPAN, Sort.INTERACTION),
        (Sort.SCALAR_QUERY, Sort.QUERY),
        (Sort.STREAM_QUERY, Sort.QUERY),
        (Sort.REDUCTION, Sort.SCALAR_QUERY),
        (Sort.SCALAR_COMMAND, Sort.COMMAND),
        (Sort.SCALAR_ACTION, Sort.ACTION),
        (Sort.STREAM_ACTION, Sort.ACTION),
        (Sort.STRATEGY, Sort.FLOW),
        (Sort.CONTROL, Sort.FLOW),
        (Sort.BRACKET, Sort.SPAN),
        (Sort.POLICY, Sort.SPAN),
    ],
)
def test_subsort_holds_for_direct_parent(sort: Sort, parent: Sort) -> None:
    assert subsort(sort, parent)


@pytest.mark.parametrize(
    "leaf",
    [
        Sort.SCALAR_QUERY,
        Sort.STREAM_QUERY,
        Sort.REDUCTION,
        Sort.SCALAR_COMMAND,
        Sort.SCALAR_ACTION,
        Sort.STREAM_ACTION,
        Sort.STRATEGY,
        Sort.CONTROL,
        Sort.BRACKET,
        Sort.POLICY,
    ],
)
def test_subsort_walks_chain_to_root(leaf: Sort) -> None:
    assert subsort(leaf, Sort.INTERACTION)


def test_subsort_reduction_descends_through_scalar_query_and_query() -> None:
    assert subsort(Sort.REDUCTION, Sort.SCALAR_QUERY)
    assert subsort(Sort.REDUCTION, Sort.QUERY)
    assert subsort(Sort.REDUCTION, Sort.INTERACTION)


def test_subsort_ref_does_not_descend_from_interaction() -> None:
    assert not subsort(Sort.REF, Sort.INTERACTION)


def test_subsort_interaction_does_not_descend_from_ref() -> None:
    assert not subsort(Sort.INTERACTION, Sort.REF)


@pytest.mark.parametrize(
    ("sort", "sibling"),
    [
        (Sort.QUERY, Sort.COMMAND),
        (Sort.COMMAND, Sort.ACTION),
        (Sort.SCALAR_QUERY, Sort.STREAM_QUERY),
        (Sort.STRATEGY, Sort.CONTROL),
        (Sort.BRACKET, Sort.POLICY),
        (Sort.SCALAR_COMMAND, Sort.SCALAR_ACTION),
        (Sort.SCALAR_ACTION, Sort.STREAM_ACTION),
    ],
)
def test_subsort_false_for_siblings(sort: Sort, sibling: Sort) -> None:
    assert not subsort(sort, sibling)


# --- matrix_sort --------------------------------------------------------


@pytest.mark.parametrize(
    ("sort", "expected"),
    [
        (Sort.REF, Sort.REF),
        (Sort.SCALAR_QUERY, Sort.SCALAR_QUERY),
        (Sort.STREAM_QUERY, Sort.STREAM_QUERY),
        (Sort.REDUCTION, Sort.SCALAR_QUERY),
        (Sort.SCALAR_COMMAND, Sort.SCALAR_COMMAND),
        (Sort.SCALAR_ACTION, Sort.SCALAR_ACTION),
        (Sort.STREAM_ACTION, Sort.STREAM_ACTION),
        (Sort.STRATEGY, Sort.STRATEGY),
        (Sort.CONTROL, Sort.CONTROL),
        (Sort.BRACKET, Sort.BRACKET),
        (Sort.POLICY, Sort.POLICY),
    ],
)
def test_matrix_sort_folds_leaf_to_matrix_row(sort: Sort, expected: Sort) -> None:
    assert matrix_sort(sort) is expected


def test_matrix_sort_folds_reduction_to_scalar_query() -> None:
    assert matrix_sort(Sort.REDUCTION) is Sort.SCALAR_QUERY


@pytest.mark.parametrize(
    "interior",
    [
        Sort.INTERACTION,
        Sort.QUERY,
        Sort.COMMAND,
        Sort.ACTION,
        Sort.FLOW,
        Sort.SPAN,
    ],
)
def test_matrix_sort_returns_none_for_interior_with_no_row(interior: Sort) -> None:
    assert matrix_sort(interior) is None


# --- MATRIX shape -------------------------------------------------------


def test_matrix_scalar_query_row_holds_value_yielders() -> None:
    row = MATRIX[Sort.SCALAR_QUERY]
    assert Sort.REF in row
    assert Sort.SCALAR_QUERY in row
    assert Sort.STREAM_QUERY in row
    assert Sort.SCALAR_ACTION in row


def test_matrix_scalar_query_row_excludes_work_only_sorts() -> None:
    row = MATRIX[Sort.SCALAR_QUERY]
    assert Sort.SCALAR_COMMAND not in row
    assert Sort.STRATEGY not in row


def test_matrix_strategy_row_holds_work_excludes_pure_values() -> None:
    row = MATRIX[Sort.STRATEGY]
    assert Sort.SCALAR_COMMAND in row
    assert Sort.STRATEGY in row
    assert Sort.SCALAR_ACTION in row
    assert Sort.SCALAR_QUERY not in row
    assert Sort.REF not in row


def test_matrix_scalar_action_in_both_value_and_work_rows() -> None:
    assert Sort.SCALAR_ACTION in MATRIX[Sort.SCALAR_QUERY]
    assert Sort.SCALAR_ACTION in MATRIX[Sort.STRATEGY]


def test_matrix_stream_action_in_both_value_and_work_rows() -> None:
    # StreamAction is the dual citizen too: a stream-shaped mutate-and-yield
    # fits a value slot (reduced by a scalar consumer) and a Strategy body.
    assert Sort.STREAM_ACTION in MATRIX[Sort.SCALAR_QUERY]
    assert Sort.STREAM_ACTION in MATRIX[Sort.STRATEGY]


@pytest.mark.parametrize("parent", [Sort.CONTROL, Sort.BRACKET, Sort.POLICY])
def test_matrix_body_holding_parents_row_is_union(parent: Sort) -> None:
    row = MATRIX[parent]
    assert row == MATRIX[Sort.SCALAR_QUERY] | MATRIX[Sort.STRATEGY]


def test_matrix_has_no_span_row() -> None:
    assert Sort.SPAN not in MATRIX


def test_matrix_ref_row_excludes_work_sorts() -> None:
    row = MATRIX[Sort.REF]
    assert Sort.SCALAR_COMMAND not in row
    assert Sort.STRATEGY not in row
    assert Sort.REF in row


# --- has_command synthesized fold ---------------------------------------


def _has_command_at_root(term: object) -> bool:
    program = nu_compile(term)
    root_id = program.id_of[program.root]
    return program.attrs[Attr.HAS_COMMAND][root_id]


def test_has_command_false_for_bare_query() -> None:
    assert _has_command_at_root(Q()) is False


def test_has_command_true_for_command_node() -> None:
    assert _has_command_at_root(Cmd(R())) is True


def test_has_command_propagates_up_through_strategy() -> None:
    assert _has_command_at_root(FlowS(Cmd(R()))) is True


def test_has_command_false_for_query_over_ref() -> None:
    assert _has_command_at_root(Q(R())) is False


def test_has_command_column_marks_command_node_itself() -> None:
    program = nu_compile(FlowS(Cmd(R())))
    column = program.attrs[Attr.HAS_COMMAND]
    assert all(isinstance(v, bool) for v in column)
    assert any(column)
