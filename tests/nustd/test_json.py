"""Functional tests for ``nustd.json`` - drive the Forms through the engine.

Covers ``loads`` / ``dumps`` with the keyword options, a round trip, a computed
argument, the async path, and the errors, asserting against the real ``json``
results.
"""

from __future__ import annotations

import asyncio
import json as pyjson

import pytest

import nustd.json as json
from nu.forms import Str
from nu.lang import Literal
from nu.lang.helpers import arun, run


DOC = {"name": "café", "tags": ["a", "b"], "n": 3, "x": 1.5, "ok": True, "none": None}
TEXT = pyjson.dumps(DOC)


def test_loads_object() -> None:
    value, _ = run(json.loads(TEXT))
    assert value == pyjson.loads(TEXT)


@pytest.mark.parametrize("text", ["[1, 2, 3]", '"hi"', "42", "1.5", "true", "null"])
def test_loads_any_top_level(text: str) -> None:
    value, _ = run(json.loads(text))
    assert value == pyjson.loads(text)


def test_loads_bytes() -> None:
    value, _ = run(json.loads(TEXT.encode()))
    assert value == DOC


def test_dumps_default() -> None:
    value, _ = run(json.dumps(DOC))
    assert value == pyjson.dumps(DOC)


def test_dumps_indent() -> None:
    value, _ = run(json.dumps(DOC, indent=2))
    assert value == pyjson.dumps(DOC, indent=2)


def test_dumps_str_indent() -> None:
    value, _ = run(json.dumps(DOC, indent="\t"))
    assert value == pyjson.dumps(DOC, indent="\t")


def test_dumps_sort_keys() -> None:
    value, _ = run(json.dumps(DOC, sort_keys=True))
    assert value == pyjson.dumps(DOC, sort_keys=True)


def test_dumps_separators() -> None:
    value, _ = run(json.dumps(DOC, separators=(",", ":")))
    assert value == pyjson.dumps(DOC, separators=(",", ":"))


def test_dumps_ensure_ascii_off() -> None:
    value, _ = run(json.dumps(DOC, ensure_ascii=False))
    assert value == pyjson.dumps(DOC, ensure_ascii=False)
    assert "café" in value


def test_dumps_all_options() -> None:
    kw = {"indent": 4, "sort_keys": True, "separators": (",", ": "), "ensure_ascii": False}
    value, _ = run(json.dumps(DOC, **kw))
    assert value == pyjson.dumps(DOC, **kw)


def test_dumps_returns_str_form() -> None:
    assert isinstance(json.dumps(DOC), Str)


def test_round_trip() -> None:
    value, _ = run(json.loads(json.dumps(DOC, indent=2)))
    assert value == DOC


def test_dumps_computed_argument() -> None:
    value, _ = run(json.dumps(json.loads(Literal(TEXT)), sort_keys=True))
    assert value == pyjson.dumps(DOC, sort_keys=True)


def test_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(json.dumps(json.loads(TEXT), indent=2)))
    assert value == pyjson.dumps(DOC, indent=2)


def test_loads_bad_input_raises_decode_error() -> None:
    with pytest.raises(json.JSONDecodeError):
        run(json.loads("{not json"))


def test_loads_bad_input_raises_on_async_path() -> None:
    with pytest.raises(json.JSONDecodeError):
        asyncio.run(arun(json.loads("[1, 2")))


def test_dumps_unencodable_raises_type_error() -> None:
    with pytest.raises(TypeError):
        run(json.dumps({"s": {1, 2}}))


def test_decode_error_is_stdlib_class() -> None:
    assert json.JSONDecodeError is pyjson.JSONDecodeError
