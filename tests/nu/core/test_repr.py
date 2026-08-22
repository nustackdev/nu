"""Execution tests for the representation atoms in nu.core.repr.

Each atom is a pure ScalarQuery, so they evaluate over Literal leaves the same
way arithmetic does. Cover the rendered value, the format-spec branching of
Format, sentinel propagation, and async parity.
"""

from __future__ import annotations

import asyncio

from nu.core.literal import Literal
from nu.core.repr import Ascii as Ascii
from nu.core.repr import Bin as Bin
from nu.core.repr import Chr as Chr
from nu.core.repr import Format as Format
from nu.core.repr import Hex as Hex
from nu.core.repr import Oct as Oct
from nu.core.repr import Ord as Ord
from nu.core.repr import Repr as Repr
from nu.lang import EMPTY, INVALID
from nu.lang.helpers import aeval, compile, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- text renderings -----------------------------------------------------


def test_repr_renders_the_repr_string():
    assert _eval(Repr(Literal("hi"))) == "'hi'"
    assert _eval(Repr(Literal(42))) == "42"


def test_ascii_escapes_non_ascii():
    assert _eval(Ascii(Literal("café"))) == "'caf\\xe9'"
    assert _eval(Ascii(Literal("hi"))) == "'hi'"


def test_format_with_no_spec_matches_format():
    assert _eval(Format(Literal(42))) == "42"
    assert _eval(Format(Literal("hi"))) == "hi"


def test_format_with_a_spec_applies_it():
    assert _eval(Format(Literal(255), Literal("x"))) == "ff"
    assert _eval(Format(Literal(3.14159), Literal(".2f"))) == "3.14"
    assert _eval(Format(Literal(5), Literal("03d"))) == "005"


# --- numeric notation ----------------------------------------------------


def test_bin_hex_oct():
    assert _eval(Bin(Literal(5))) == "0b101"
    assert _eval(Hex(Literal(255))) == "0xff"
    assert _eval(Oct(Literal(8))) == "0o10"


# --- code points ---------------------------------------------------------


def test_ord_and_chr_round_trip():
    assert _eval(Ord(Literal("A"))) == 65
    assert _eval(Chr(Literal(65))) == "A"
    assert _eval(Chr(Ord(Literal("z")))) == "z"


# --- sentinel propagation ------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(Repr(Literal(EMPTY))) is INVALID
    assert _eval(Hex(Literal(INVALID))) is INVALID
    assert _eval(Format(Literal(EMPTY))) is INVALID
    assert _eval(Format(Literal(1), Literal(EMPTY))) is INVALID
    assert _eval(Format(Literal(INVALID), Literal("x"))) is INVALID


# --- async parity --------------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(Repr(Literal("hi")))) == "'hi'"
    assert asyncio.run(_aeval(Hex(Literal(255)))) == "0xff"
    assert asyncio.run(_aeval(Format(Literal(255), Literal("x")))) == "ff"
    assert asyncio.run(_aeval(Format(Literal(EMPTY)))) is INVALID
