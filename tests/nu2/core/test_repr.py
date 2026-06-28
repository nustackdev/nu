"""Execution tests for the representation atoms in nu2.core.repr.

Each atom is a pure ScalarQuery, so they evaluate over LiteralQuery leaves the same
way arithmetic does. Cover the rendered value, the format-spec branching of
Format, sentinel propagation, and async parity.
"""

from __future__ import annotations

import asyncio

from nu2.core.literal import LiteralQuery
from nu2.core.repr import AsciiQuery as Ascii
from nu2.core.repr import BinQuery as Bin
from nu2.core.repr import ChrQuery as Chr
from nu2.core.repr import FormatQuery as Format
from nu2.core.repr import HexQuery as Hex
from nu2.core.repr import OctQuery as Oct
from nu2.core.repr import OrdQuery as Ord
from nu2.core.repr import ReprQuery as Repr
from nu2.lang import EMPTY, INVALID, compile
from nu2.lang.helpers import aeval, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- text renderings -----------------------------------------------------


def test_repr_renders_the_repr_string():
    assert _eval(Repr(LiteralQuery("hi"))) == "'hi'"
    assert _eval(Repr(LiteralQuery(42))) == "42"


def test_ascii_escapes_non_ascii():
    assert _eval(Ascii(LiteralQuery("café"))) == "'caf\\xe9'"
    assert _eval(Ascii(LiteralQuery("hi"))) == "'hi'"


def test_format_with_no_spec_matches_format():
    assert _eval(Format(LiteralQuery(42))) == "42"
    assert _eval(Format(LiteralQuery("hi"))) == "hi"


def test_format_with_a_spec_applies_it():
    assert _eval(Format(LiteralQuery(255), LiteralQuery("x"))) == "ff"
    assert _eval(Format(LiteralQuery(3.14159), LiteralQuery(".2f"))) == "3.14"
    assert _eval(Format(LiteralQuery(5), LiteralQuery("03d"))) == "005"


# --- numeric notation ----------------------------------------------------


def test_bin_hex_oct():
    assert _eval(Bin(LiteralQuery(5))) == "0b101"
    assert _eval(Hex(LiteralQuery(255))) == "0xff"
    assert _eval(Oct(LiteralQuery(8))) == "0o10"


# --- code points ---------------------------------------------------------


def test_ord_and_chr_round_trip():
    assert _eval(Ord(LiteralQuery("A"))) == 65
    assert _eval(Chr(LiteralQuery(65))) == "A"
    assert _eval(Chr(Ord(LiteralQuery("z")))) == "z"


# --- sentinel propagation ------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(Repr(LiteralQuery(EMPTY))) is INVALID
    assert _eval(Hex(LiteralQuery(INVALID))) is INVALID
    assert _eval(Format(LiteralQuery(EMPTY))) is INVALID
    assert _eval(Format(LiteralQuery(1), LiteralQuery(EMPTY))) is INVALID
    assert _eval(Format(LiteralQuery(INVALID), LiteralQuery("x"))) is INVALID


# --- async parity --------------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(Repr(LiteralQuery("hi")))) == "'hi'"
    assert asyncio.run(_aeval(Hex(LiteralQuery(255)))) == "0xff"
    assert asyncio.run(_aeval(Format(LiteralQuery(255), LiteralQuery("x")))) == "ff"
    assert asyncio.run(_aeval(Format(LiteralQuery(EMPTY)))) is INVALID
