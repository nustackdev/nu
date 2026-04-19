"""Basic Nu example - pure arithmetic under the new evaluator.

Shows the core pattern: build a tree, open it, take the value.
"""

import asyncio

import nu


async def main() -> None:
    ctx = nu.Context()

    # Build (3 + 4) * 2
    expr = nu.MulOp(nu.AddOp(nu.Literal(3), nu.Literal(4)), nu.Literal(2))

    # single-yield value via `first`
    print(f"(3 + 4) * 2 = {await nu.first(expr, ctx)}")

    # `collect` gives a list (one element for a yield-once tree)
    print(f"collect: {await nu.collect(expr, ctx)}")

    # `execute` drains and returns None (algebra-faithful)
    result = await nu.execute(expr, ctx)
    print(f"execute returns: {result}")

    # Sequential composition with `>>`
    seq = nu.Literal(1) >> nu.Literal(2) >> nu.Literal(3)
    print(f"1 >> 2 >> 3 collect: {await nu.collect(seq, ctx)}")

    # Parallel composition with `|` (interleaves)
    par = nu.Literal("a") | nu.Literal("b") | nu.Literal("c")
    print(f"a | b | c collect: {sorted(await nu.collect(par, ctx))}")

    # Purity
    print(f"Pure: {nu.is_pure(expr)}")


asyncio.run(main())
