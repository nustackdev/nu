"""Query strings: one encoding, the same on both sides of the wire.

The bytes are the browser's own ``URLSearchParams`` (the
application/x-www-form-urlencoded set): a space is ``+``, letters, digits and
``*-._`` stay as they are, and every other byte of the UTF-8 is ``%XX``. The
kit's TS query helpers write the same bytes, and one set of fixtures
(``tests/fixtures/query.json`` at the nu repo root) holds both to it.

A query is a flat dict of strings. Decoding keeps the last value of a key
that repeats. Encoding spells a few plain values one way:

- a str as is
- True / False as ``"true"`` / ``"false"``
- an int in decimal; a float that is whole as an int (``2.0`` is ``"2"``,
  as JS prints it), any other float as Python's ``repr`` (exponent forms
  differ from JS: pass a str for those)
- None drops the key
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING
from urllib.parse import unquote_plus


if TYPE_CHECKING:
    from collections.abc import Mapping


__all__ = ["decode_query", "encode_query", "query_value"]


_SAFE = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789*-._")


def query_value(value: object) -> str | None:
    """``value`` as the query spells it, or None for a key that drops."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer():
            return str(int(value))
        return repr(value)
    return str(value)


def _quote(text: str) -> str:
    out: list[str] = []
    for byte in text.encode("utf-8"):
        if byte in _SAFE:
            out.append(chr(byte))
        elif byte == 0x20:
            out.append("+")
        else:
            out.append(f"%{byte:02X}")
    return "".join(out)


def encode_query(values: Mapping[str, object] | None = None, /, **kv: object) -> str:
    """The query string for ``values`` and ``kv``, no leading ``?``, in key order.

    ``encode_query(id=42, q="a b")`` is ``"id=42&q=a+b"``. A None value drops
    its key. Build a link with it: ``f"/movie?{encode_query(id=42)}"``.
    """
    merged = {**(values or {}), **kv}
    parts: list[str] = []
    for key, raw in merged.items():
        value = query_value(raw)
        if value is not None:
            parts.append(f"{_quote(str(key))}={_quote(value)}")
    return "&".join(parts)


def decode_query(search: str) -> dict[str, str]:
    """``search`` (with or without the leading ``?``) as a dict; a repeated key keeps its last value."""
    out: dict[str, str] = {}
    for piece in search.removeprefix("?").split("&"):
        if piece == "":
            continue
        key, _, value = piece.partition("=")
        out[unquote_plus(key)] = unquote_plus(value)
    return out
