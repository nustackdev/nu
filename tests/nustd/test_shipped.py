"""A Teleport body with args crosses as one term, the generated Shape pickled by value with it."""

from __future__ import annotations

import subprocess
import sys

import nu
from nu.lang import wire
from nustd._shipped import Shipped, shipped
from nustd.mp import Teleport


def _built() -> Teleport:
    return Teleport(None, lambda n, rows: nu.List.of(nu.Add(n, 1), rows), 0, n=41, rows=[1, 2])


def test_a_tree_body_crosses_as_itself():
    tele = Teleport(None, nu.Add(1, 2), 0)
    body = nu.tree.children(tele)[0]
    assert shipped(tele._ship, [], body) is body


def test_the_shipped_term_holds_the_binding_and_the_values():
    tele = _built()
    term = shipped(tele._ship, [41, [1, 2]], nu.tree.children(tele)[0])
    assert isinstance(term, Shipped)
    assert term._values == (41, [1, 2])
    assert term._binding.slots == ("n", "rows")


def test_the_generated_shape_is_not_importable_so_it_pickles_by_value():
    shape = _built()._ship.shape
    assert shape.__module__ == "nu.lang.binding"
    assert not hasattr(sys.modules[shape.__module__], shape.__qualname__)


def test_a_shipped_term_runs_after_a_round_trip_in_process():
    tele = _built()
    term = wire.loads(wire.dumps(shipped(tele._ship, [41, [1, 2]], nu.tree.children(tele)[0])))
    assert nu.run(term)[0] == [42, [1, 2]]


_REMOTE = """
import sys
from nu.lang import wire
import nu
term = wire.loads(sys.stdin.buffer.read())
print(nu.run(term)[0])
"""


def test_a_shipped_term_runs_in_a_fresh_process():
    """The receiving process never built the lambda: the Shape comes only from the bytes."""
    tele = _built()
    data = wire.dumps(shipped(tele._ship, [41, [1, 2]], nu.tree.children(tele)[0]))
    out = subprocess.run(  # noqa: S603
        [sys.executable, "-c", _REMOTE], input=data, capture_output=True, check=True, timeout=60
    )
    assert out.stdout.decode().strip() == "[42, [1, 2]]"
