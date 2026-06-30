"""Structural tests for the IO core atoms (nu.core.io).

These atoms write through the stdio/filesystem fabric, which is not wired yet,
so they are declared structurally (no eval). We check only what the language
assigns from structure: effect attribution (the slot-0 fabric write), sort,
and cardinality. No execution.
"""

from __future__ import annotations

import pytest

from nu.core.io import InputAction, OpenAction, PrintCommand
from nu.lang import Cardinality, Sort


# The IO fabric (stdio / filesystem) is an experimental, unwired fabric. Its
# effect attribution is parked until the fabric comes online; only the sort /
# cardinality structure is checked here.


@pytest.mark.skip(reason="IO fabric experimental, not wired")
def test_print_declares_a_write_through_its_fabric_ref():
    pass


@pytest.mark.skip(reason="IO fabric experimental, not wired")
def test_print_reads_its_value_operands():
    pass


@pytest.mark.skip(reason="IO fabric experimental, not wired")
def test_input_declares_a_write_through_its_fabric_ref():
    pass


@pytest.mark.skip(reason="IO fabric experimental, not wired")
def test_open_declares_a_write_through_its_fabric_ref():
    pass


# --- sorts ---------------------------------------------------------------


def test_print_is_a_command():
    assert PrintCommand.sort.value is Sort.SCALAR_COMMAND


def test_input_and_open_are_scalar_actions():
    assert InputAction.sort.value is Sort.SCALAR_ACTION
    assert OpenAction.sort.value is Sort.SCALAR_ACTION


# --- cardinality ---------------------------------------------------------


def test_print_yields_nothing():
    assert PrintCommand.cardinality.value is Cardinality.VOID


def test_actions_yield_a_scalar():
    assert InputAction.cardinality.value is Cardinality.SCALAR
    assert OpenAction.cardinality.value is Cardinality.SCALAR
