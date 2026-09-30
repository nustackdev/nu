"""``nu.lang.wire``: cloudpickle both ways, for every transport."""

from __future__ import annotations

import multiprocessing
import pickle

import nu
from nu.lang import wire


def test_a_class_defined_in_a_function_round_trips() -> None:
    class Point:
        def __init__(self, x: int) -> None:
            self.x = x

    back = wire.loads(wire.dumps(Point(3)))
    assert back.x == 3


def test_the_bytes_are_plain_pickle_data() -> None:
    def double(x: int) -> int:
        return 2 * x

    assert pickle.loads(wire.dumps(double))(21) == 42  # noqa: S301


def test_a_tree_over_a_local_shape_round_trips() -> None:
    class Tally(nu.Shape):
        n = nu.mem.IntRef.slot()

    term = nu.mem.Frame(Tally, nu.Add(Tally.n, 1), n=41)
    assert nu.run(wire.loads(wire.dumps(term)))[0] == 42


def test_send_and_recv_over_a_connection() -> None:
    class Local:
        pass

    left, right = multiprocessing.Pipe()
    try:
        wire.send(left, ("frame", Local))
        kind, cls = wire.recv(right)
    finally:
        left.close()
        right.close()
    assert kind == "frame"
    assert cls.__name__ == "Local"
