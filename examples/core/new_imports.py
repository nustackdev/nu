"""Example: new module structure imports.

Demonstrates the post-reorg import paths. Old paths (nu.abc, nu.core, etc.)
still work through shims but new code should use these paths.
"""

from __future__ import annotations

import asyncio

# terms — the building blocks of the algebra
from nu.terms import Term, Value, Ref, Morphism, Operation, Command
from nu.terms import EMPTY, INVALID, Sentinel, Span
from nu.terms import IntArg, StrArg, BoolArg

# context — runtime resource container
from nu.context import Context, Attributes

# ops — all concrete operations
from nu.ops import AddOp, MulOp, EqOp, LtOp, GtOp, LenOp
from nu.ops import Seq, If, ForEach, ForRange, Parallel, While, Print
from nu import fn  # functional wrappers

# interfaces — type system
from nu.interfaces import IntI, StrI, FloatI
from nu.interfaces import IntI, StrI, FloatI, ListI, BoolI

# model
from nu.model import Model

# transform — tree transformations
from nu.transform import preorder, postorder, format_tree, map_nodes

# convenience: top-level nu re-exports the essentials
from nu import Term, Context, Node, print_tree


async def main() -> None:
    ctx = Context()

    # compose lazy expression trees
    price = FloatI(42.50)
    qty = IntI(3)
    subtotal = price * qty
    tax = subtotal * FloatI(0.08)
    total = subtotal + tax

    # evaluate
    result = await total.execute(ctx)
    print(f"total: {result}")

    # flows compose the same way
    flow = Seq(
        Print("price", price),
        Print("total", total),
        If(total > 100, Print("expensive!"), Print("cheap")),
    )
    await flow.execute(ctx)

    # tree inspection
    print("\n--- expression tree ---")
    print_tree(total)

    # functional wrappers
    nums = ListI([3, 1, 4, 1, 5])
    sorted_nums = fn.Sorted(nums)
    print(f"\nsorted: {await sorted_nums.execute(ctx)}")


if __name__ == "__main__":
    asyncio.run(main())
