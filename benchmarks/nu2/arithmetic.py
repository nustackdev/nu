"""Arithmetic benchmark: pure python vs Nu v1 vs Nu v2.

Builds three random arithmetic trees (small, medium, large) and runs each
under three engines:

- ``py``  - a plain Python callable returning the same value
- ``nu1`` - the v1 ``nu`` package, driven via ``runtime.first``
- ``nu2`` - the v2 ``nu2`` package, driven via ``nu2.lang.entry.run``

For Nu v2 we also break the cost down into ``attribute + validate`` (one-time
setup) and ``eval`` (steady-state) so the optimization surface is visible.

Run: ``uv run python benchmarks/nu2/arithmetic.py``.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

import nu as nu1
from nu import runtime as nu1_runtime
from nu2.core import Add, Literal, Mul, Neg, Sub
from nu2.lang import LAWS, attribute, validate
from nu2.lang.entry import eval as nu2_eval
from nu2.lang.entry import run as nu2_run


# --- tree generation --------------------------------------------------------


@dataclass
class Spec:
    """A benchmark tree spec: name, depth budget, branching cap, RNG seed."""

    name: str
    depth: int
    branching: int
    seed: int


SPECS = (
    Spec("small", depth=3, branching=2, seed=1),
    Spec("medium", depth=6, branching=2, seed=2),
    Spec("large", depth=9, branching=2, seed=3),
)


def _build(spec: Spec):
    """Build (py_callable, nu1_tree, nu2_tree, expected_value, node_count).

    The three forms encode the same arithmetic expression; the python callable
    is a zero-argument lambda capturing literals so the call overhead matches
    what Nu has to do.
    """
    rng = random.Random(spec.seed)  # noqa: S311
    count = [0]

    def gen(depth: int):
        count[0] += 1
        if depth == 0:
            v = rng.randint(1, 9)
            return (lambda v=v: v), Literal(v), nu1.Literal(v)
        op = rng.choice(("add", "sub", "mul", "neg"))
        if op == "neg":
            py, t2, t1 = gen(depth - 1)
            return (lambda py=py: -py()), Neg(t2), nu1.Neg(t1)
        # Nu v1 arithmetic ops are strictly binary; keep both engines apples to
        # apples by restricting to arity 2 here.
        left = gen(depth - 1)
        right = gen(depth - 1)
        lp, l2, l1 = left
        rp, r2, r1 = right
        if op == "add":
            return (lambda lp=lp, rp=rp: lp() + rp()), Add(l2, r2), nu1.Add(l1, r1)
        if op == "sub":
            return (lambda lp=lp, rp=rp: lp() - rp()), Sub(l2, r2), nu1.Sub(l1, r1)
        if op == "mul":
            return (lambda lp=lp, rp=rp: lp() * rp()), Mul(l2, r2), nu1.Mul(l1, r1)
        raise AssertionError(op)

    py, n2, n1 = gen(spec.depth)
    return py, n1, n2, py(), count[0]


# --- timing -----------------------------------------------------------------


def _bench(label: str, fn, iters: int) -> float:
    """Run ``fn`` ``iters`` times and return mean seconds per call."""
    # Warmup
    for _ in range(min(20, iters)):
        fn()
    t0 = time.perf_counter()
    for _ in range(iters):
        fn()
    dt = time.perf_counter() - t0
    return dt / iters


def _fmt(seconds: float) -> str:
    if seconds < 1e-6:
        return f"{seconds * 1e9:7.1f} ns"
    if seconds < 1e-3:
        return f"{seconds * 1e6:7.2f} us"
    return f"{seconds * 1e3:7.3f} ms"


def main() -> None:
    print(f"{'spec':<8}{'nodes':>7}  {'engine':<14}{'per-call':>12}{'ops/s':>14}{'vs py':>10}")
    print("-" * 72)

    for spec in SPECS:
        py_fn, n1_tree, n2_tree, expected, nodes = _build(spec)

        # Sanity: all three agree.
        nu1_val = nu1_runtime.first(n1_tree)
        nu2_val, _ = nu2_run(n2_tree)
        assert py_fn() == expected, (py_fn(), expected)
        assert nu1_val == expected, (nu1_val, expected)
        assert nu2_val == expected, (nu2_val, expected)

        iters = max(200, 50_000 // max(nodes, 1))

        py_t = _bench("py", py_fn, iters * 20)
        n1_t = _bench("nu1.first", lambda t=n1_tree: nu1_runtime.first(t), iters)
        n2_total = _bench("nu2.run", lambda t=n2_tree: nu2_run(t), iters)

        # Split nu2 into setup vs eval.
        attributed = validate(attribute(n2_tree), *LAWS)
        n2_eval_t = _bench("nu2.eval", lambda p=attributed: nu2_eval(p), iters)
        n2_setup_t = max(0.0, n2_total - n2_eval_t)

        rows = (
            ("py", py_t),
            ("nu1.first", n1_t),
            ("nu2.run", n2_total),
            ("  attr+valid", n2_setup_t),
            ("  eval", n2_eval_t),
        )
        for i, (engine, t) in enumerate(rows):
            head = f"{spec.name:<8}{nodes:>7}  " if i == 0 else " " * 17
            ratio = f"{t / py_t:>8.1f}x" if py_t > 0 else "       -"
            ops = f"{1.0 / t:>12,.0f}" if t > 0 else " " * 12
            print(f"{head}{engine:<14}{_fmt(t):>12}{ops:>14}{ratio:>10}")
        print()


if __name__ == "__main__":
    main()
