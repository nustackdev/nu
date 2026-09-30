"""What binders hand their bodies through ``ctx.attrs``.

An interaction hands over immutable values: what it builds itself is bound in
an immutable form, and user data passes through untouched. These pin both
halves on the core binders.
"""

from __future__ import annotations

import asyncio

import nu
import nustd.mem as nm


class Seen(nu.Shape):
    log = nm.ListRef.slot(object)


def test_a_loop_hands_the_item_through_as_it_is() -> None:
    row = {"id": 1}
    term = nu.Collect(nu.Map(nu.Iter([row]), nu.Attr("item")))
    assert nu.run(term)[0][0] is row
    assert asyncio.run(nu.arun(term))[0][0] is row


def test_a_range_loop_hands_over_plain_ints() -> None:
    data: dict = {"log": []}
    ctx = nu.Context().bind(dict, data, Seen)
    nu.run(nu.ForRangeDo(0, 2, Seen.log.append(nu.Attr("index"))), ctx)
    assert data["log"] == [0, 1]
    assert all(type(i) is int for i in data["log"])


def test_a_catch_hands_over_the_error_as_a_string() -> None:
    caught = nu.run(nu.TryCatch(nu.raise_(ValueError, "boom"), catch=nu.Attr("error")))[0]
    assert isinstance(caught, str)
    assert caught == "boom"
    assert isinstance(caught.exception, ValueError)
