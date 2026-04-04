"""Lambda filter vs Nu filter -- the difference.

FilterOp: predicate is a Python lambda. opaque to the tree.
Filter (Calculation): predicate is a Nu. visible to Deformations, can access Substrates.

Both filter the same data. one is Python, the other is Nu all the way down.

Run:
    python examples/core/filter_lambda_vs_nu.py
"""

from __future__ import annotations

import asyncio
import time

from nu import AnyAttrRef, Context, fn
from nu.ops import Print
from nu.terms.op import Calculation
from nu.interfaces import AnyI
from nu.ops import AtOp
from nu.utils import ensure_nu


# ---------------------------------------------------------------------------
# Filter Calculation -- defined here, not in the library yet
# ---------------------------------------------------------------------------


class Filter(Calculation):
    """Execute body for each item where a Nu condition is truthy.

    children: [items, condition, body, item_key]

    The condition is a Nu -- a tree node. Deformations see it.
    Compare to FilterOp where the predicate is a Python lambda (opaque).
    """

    def __init__(self, items, *, condition, body, item="item"):
        super().__init__(
            ensure_nu(items),
            condition,
            body,
            ensure_nu(item),
        )

    async def execute(self, ctx):
        items = await self.children[0].execute(ctx)
        condition = self.children[1]
        body = self.children[2]
        item_key = await self.children[3].execute(ctx)

        for elem in items:
            ctx.attrs[item_key] = elem
            if await condition.execute(ctx):
                await body.execute(ctx)


# ---------------------------------------------------------------------------
# helper: tx["key"] as a Nu expression (AnyI lacks __getitem__)
# ---------------------------------------------------------------------------


def tx_field(field: str) -> AnyI:
    """Access a field on the current tx in ctx.attrs.

    tx_field("fee") builds: AnyI(AtOp(AnyAttrRef("tx").get(), "fee"))
    """
    return AnyI(AtOp(AnyAttrRef("tx").get(), field))


# ---------------------------------------------------------------------------
# sample data
# ---------------------------------------------------------------------------

TXNS = [
    {"sig": "abc1", "fee": 5000, "program": "pump", "sol": 1.2},
    {"sig": "abc2", "fee": 0, "program": "system", "sol": 0.0},
    {"sig": "abc3", "fee": 15000, "program": "pump", "sol": 3.5},
    {"sig": "abc4", "fee": 200, "program": "raydium", "sol": 0.8},
    {"sig": "abc5", "fee": 8000, "program": "pump", "sol": 2.1},
    {"sig": "abc6", "fee": 0, "program": "system", "sol": 0.0},
    {"sig": "abc7", "fee": 500, "program": "jupiter", "sol": 0.3},
]


async def main():
    ctx = Context()

    ITERS = 1000

    # ===================================================================
    # 1. LAMBDA FILTER (FilterOp via fn.Filter)
    #
    #    predicate is a Python lambda -- opaque to the tree.
    #    returns a lazy iterator. pure Calc. fast.
    #    but: Deformations can't see inside the lambda.
    # ===================================================================

    print("=== Lambda filter (FilterOp) ===")
    print("pump txs with fee > 1000:\n")

    filtered = fn.Filter(
        TXNS,
        lambda t: t["program"] == "pump" and t["fee"] > 1000,
    )

    result = await fn.ToList(filtered).execute(ctx)
    for tx in result:
        print(f"  {tx['sig']}  fee={tx['fee']}  sol={tx['sol']}")

    # ===================================================================
    # 2. NU FILTER (Filter Calculation)
    #
    #    condition is a Nu -- every piece is a tree node.
    #    tx_field("program").eq("pump") builds:
    #       BoolI(EqOp(AnyI(AtOp(AnyAttrRef("tx").get(), "program")), "pump"))
    #    Deformations see the whole thing. no lambdas anywhere.
    # ===================================================================

    print("\n=== Nu filter (Filter Calculation) ===")
    print("pump txs with fee > 1000:\n")

    tree = Filter(
        TXNS,
        condition=tx_field("program").eq("pump").and_(tx_field("fee") > 1000),
        body=Print("match", tx_field("sig"), tx_field("fee"), tx_field("sol")),
        item="tx",
    )

    await tree.execute(ctx)

    # ===================================================================
    # 3. PERF: 1000 iterations, no printing
    # ===================================================================

    print(f"\n=== Perf: {ITERS} iterations ===\n")

    # -- lambda filter --
    lambda_tree = fn.ToList(fn.Filter(
        TXNS,
        lambda t: t["program"] == "pump" and t["fee"] > 1000,
    ))

    t0 = time.perf_counter()
    for _ in range(ITERS):
        await lambda_tree.execute(ctx)
    lambda_ms = (time.perf_counter() - t0) * 1000

    # -- nu filter (no-op body, just condition evaluation) --
    noop = Calculation()  # empty flow, does nothing

    nu_tree = Filter(
        TXNS,
        condition=tx_field("program").eq("pump").and_(tx_field("fee") > 1000),
        body=noop,
        item="tx",
    )

    t0 = time.perf_counter()
    for _ in range(ITERS):
        await nu_tree.execute(ctx)
    nu_ms = (time.perf_counter() - t0) * 1000

    # -- raw python baseline --
    t0 = time.perf_counter()
    for _ in range(ITERS):
        [t for t in TXNS if t["program"] == "pump" and t["fee"] > 1000]
    raw_ms = (time.perf_counter() - t0) * 1000

    # -- sync nu simulation --
    # same tree shape, same execute() dispatch, just no async/await.
    # isolates coroutine overhead from tree-walk overhead.

    class SyncValue:
        __slots__ = ("_v",)
        def __init__(self, v): self._v = v
        def execute(self, attrs): return self._v

    class SyncAttrGet:
        __slots__ = ("_key",)
        def __init__(self, key): self._key = key
        def execute(self, attrs): return attrs[self._key]

    class SyncAt:
        __slots__ = ("_obj", "_key")
        def __init__(self, obj, key): self._obj = obj; self._key = key
        def execute(self, attrs): return self._obj.execute(attrs)[self._key.execute(attrs)]

    class SyncEq:
        __slots__ = ("_l", "_r")
        def __init__(self, l, r): self._l = l; self._r = r
        def execute(self, attrs): return self._l.execute(attrs) == self._r.execute(attrs)

    class SyncGt:
        __slots__ = ("_l", "_r")
        def __init__(self, l, r): self._l = l; self._r = r
        def execute(self, attrs): return self._l.execute(attrs) > self._r.execute(attrs)

    class SyncAnd:
        __slots__ = ("_l", "_r")
        def __init__(self, l, r): self._l = l; self._r = r
        def execute(self, attrs): return self._l.execute(attrs) and self._r.execute(attrs)

    def sync_field(name):
        return SyncAt(SyncAttrGet("tx"), SyncValue(name))

    sync_cond = SyncAnd(
        SyncEq(sync_field("program"), SyncValue("pump")),
        SyncGt(sync_field("fee"), SyncValue(1000)),
    )

    attrs = {}
    t0 = time.perf_counter()
    for _ in range(ITERS):
        for elem in TXNS:
            attrs["tx"] = elem
            sync_cond.execute(attrs)
    sync_ms = (time.perf_counter() - t0) * 1000

    # -- count execute() calls --
    call_count = 0
    original_op_execute = type(nu_tree.children[1]).__mro__[1].execute  # BoolI -> Interface -> Op

    from nu.terms.op import NAryOp
    from nu.terms.value import Value
    from nu.terms.ref import Ref

    _orig_op = NAryOp.execute
    _orig_val = Value.execute
    _orig_ref = Ref.execute

    async def _counted_op(self, ctx):
        nonlocal call_count
        call_count += 1
        return await _orig_op(self, ctx)

    async def _counted_val(self, ctx):
        nonlocal call_count
        call_count += 1
        return await _orig_val(self, ctx)

    async def _counted_ref(self, ctx):
        nonlocal call_count
        call_count += 1
        return await _orig_ref(self, ctx)

    NAryOp.execute = _counted_op
    Value.execute = _counted_val
    Ref.execute = _counted_ref

    call_count = 0
    await nu_tree.execute(ctx)
    nu_calls = call_count

    call_count = 0
    await lambda_tree.execute(ctx)
    lambda_calls = call_count

    NAryOp.execute = _orig_op
    Value.execute = _orig_val
    Ref.execute = _orig_ref

    print(f"  raw python:    {raw_ms:7.2f} ms")
    print(f"  lambda filter: {lambda_ms:7.2f} ms  ({lambda_calls} execute() calls)")
    print(f"  sync nu:       {sync_ms:7.2f} ms  (same tree, no async/await)")
    print(f"  async nu:      {nu_ms:7.2f} ms  ({nu_calls} execute() calls)")
    print()
    print(f"  async/sync:    {nu_ms / sync_ms:.1f}x  <-- pure coroutine overhead")
    print(f"  sync/raw:      {sync_ms / raw_ms:.1f}x  <-- tree-walk overhead")
    print(f"  async/raw:     {nu_ms / raw_ms:.1f}x  <-- total")

    # ===================================================================
    # 4. TREE COMPARISON
    # ===================================================================

    print("\n=== Tree comparison ===\n")

    print("lambda filter tree:")
    print(f"  {filtered!r}")

    print("\nnu filter tree:")
    print(f"  condition: {tree.children[1]!r}")


if __name__ == "__main__":
    asyncio.run(main())
