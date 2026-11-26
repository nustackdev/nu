"""What bindings hand their bodies through their frames.

An interaction hands over immutable values: what it builds itself is handed
in an immutable form, and user data passes through untouched. These pin both
halves on the core bindings.
"""

from __future__ import annotations

import asyncio

import nu
import nu.mem as nm


class Seen(nu.Shape):
    log = nm.ListRef.slot(object)
    rows = nm.ListRef.slot(object)


class _Row:
    """A user object: no builtin container, so nothing on the way copies it."""


def test_a_loop_hands_the_item_through_as_it_is() -> None:
    row = _Row()
    term = nu.Collect(nu.Map(nu.Iter([row]), lambda item: item))
    assert nu.run(term)[0][0] is row
    assert asyncio.run(nu.arun(term))[0][0] is row


def test_a_loop_over_a_ref_hands_the_stored_items_through() -> None:
    row = {"id": 1}
    data: dict = {"rows": [row]}
    ctx = nu.Context().bind(dict, data, Seen)
    term = nu.Collect(nu.Map(nu.Iter(Seen.rows), lambda item: item))
    assert nu.run(term, ctx)[0][0] is row
    assert asyncio.run(nu.arun(term, ctx))[0][0] is row


def test_a_range_loop_hands_over_plain_ints() -> None:
    data: dict = {"log": []}
    ctx = nu.Context().bind(dict, data, Seen)
    nu.run(nu.ForRangeDo(0, 2, lambda i: Seen.log.append(i)), ctx)
    assert data["log"] == [0, 1]
    assert all(type(i) is int for i in data["log"])


def test_a_catch_hands_over_the_error_as_a_string() -> None:
    caught = nu.run(nu.TryCatch(nu.raise_(ValueError, "boom"), catch=lambda error: error))[0]
    assert isinstance(caught, str)
    assert caught == "boom"
    assert isinstance(caught.exception, ValueError)
