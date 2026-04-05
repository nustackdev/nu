"""Iterflows demo -- Nu-native iteration constructs.

Shows Filter, Map, TakeWhile, Unique from flowsx.iterflows.
Every predicate/transform is a Nu -- no lambdas, no holes in the tree.

Run:
    uv run python examples/core/iterflows_demo.py
"""

from __future__ import annotations

import asyncio

from nu import AnyAttrRef, Context
from nu.ops import Print, Seq, Filter, Map, TakeWhile, Unique
from nu.interfaces import AnyI
from nu.ops import AtOp


# ---------------------------------------------------------------------------
# helper: access a field on the current item in ctx.attrs
# ---------------------------------------------------------------------------


def tx_field(field: str) -> AnyI:
    """Build a Nu expression for ctx.attrs["tx"][field]."""
    return AnyI(AtOp(AnyAttrRef("tx"), field))


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

    # =======================================================================
    # 1. FILTER -- pump txs with fee > 1000
    #
    #    condition is a Nu: tx_field("program").eq("pump").and_(fee > 1000)
    #    Deformations see the whole predicate. no lambda.
    # =======================================================================

    print("=== Filter: pump txs with fee > 1000 ===\n")

    await Filter(
        TXNS,
        condition=tx_field("program").eq("pump").and_(tx_field("fee") > 1000),
        body=Print("  ", tx_field("sig"), "fee=", tx_field("fee"), "sol=", tx_field("sol")),
        item="tx",
    ).execute(ctx)

    # =======================================================================
    # 2. MAP -- extract fees from all txs
    #
    #    transform is a Nu: tx_field("fee")
    #    results collected in ctx.attrs["fees"]
    # =======================================================================

    print("\n=== Map: extract all fees ===\n")

    await Seq(
        Map(TXNS, transform=tx_field("fee"), output="fees", item="tx"),
        Print("  fees:", AnyAttrRef("fees").get()),
    ).execute(ctx)

    # =======================================================================
    # 3. TAKEWHILE -- process txs while fee > 0
    #
    #    stops at the first tx with fee == 0 (abc2).
    #    useful for sorted/ordered data.
    # =======================================================================

    print("\n=== TakeWhile: process while fee > 0 ===\n")

    await TakeWhile(
        TXNS,
        condition=tx_field("fee") > 0,
        body=Print("  processing:", tx_field("sig"), "fee=", tx_field("fee")),
        item="tx",
    ).execute(ctx)

    print("  (stopped at first zero-fee tx)")

    # =======================================================================
    # 4. UNIQUE -- unique programs
    #
    #    key is a Nu: tx_field("program")
    #    executes body once per unique program.
    # =======================================================================

    print("\n=== Unique: distinct programs ===\n")

    await Unique(
        TXNS,
        key=tx_field("program"),
        body=Print("  program:", tx_field("program")),
        item="tx",
    ).execute(ctx)

    # =======================================================================
    # 5. COMPOSITION -- Filter + Map in sequence
    #
    #    filter+body is the composition primitive.
    #    the body IS the action -- no separate "collect" step needed.
    #    but you can also chain: Map to collect, then process.
    # =======================================================================

    print("\n=== Composition: Map fees -> print ===\n")

    await Seq(
        Map(TXNS, transform=tx_field("fee"), output="all_fees", item="tx"),
        Print("  all fees:", AnyAttrRef("all_fees").get()),
    ).execute(ctx)

    print("\n=== Composition: Filter pump -> print each ===\n")

    await Filter(
        TXNS,
        condition=tx_field("program").eq("pump"),
        body=Print("  pump:", tx_field("sig"), "fee=", tx_field("fee")),
        item="tx",
    ).execute(ctx)


if __name__ == "__main__":
    asyncio.run(main())
